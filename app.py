import streamlit as st
import pandas as pd
import os
import time
import uuid
from pathlib import Path
import hashlib # For password hashing

# --- Configuration & Initial Setup ---

st.set_page_config(
    page_title="మాట - కమ్యూనిటీ", # "Maata - Community"
    page_icon="👋",
    layout="centered",
    initial_sidebar_state="auto"
)

STORAGE_DIR = Path("storage/uploads")
USER_CSV = STORAGE_DIR / "users.csv"
POSTS_CSV = STORAGE_DIR / "posts.csv"
INTERACTIONS_CSV = STORAGE_DIR / "interactions.csv"

STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Initialize users.csv - ADD 'about' and 'dob' columns
if not USER_CSV.exists():
    pd.DataFrame(columns=["username", "password", "email", "about", "dob"]).to_csv(USER_CSV, index=False)
else:
    # Ensure existing users.csv has 'about' and 'dob' columns
    users_df_check = pd.read_csv(USER_CSV)
    columns_to_add = []
    if 'about' not in users_df_check.columns:
        columns_to_add.append('about')
    if 'dob' not in users_df_check.columns:
        columns_to_add.append('dob')
    if columns_to_add:
        for col in columns_to_add:
            users_df_check[col] = ''
        users_df_check.to_csv(USER_CSV, index=False)


if not POSTS_CSV.exists():
    pd.DataFrame(columns=["post_id", "username", "timestamp", "caption", "media_path"]).to_csv(POSTS_CSV, index=False)

# Initialize interactions.csv
if not INTERACTIONS_CSV.exists():
    pd.DataFrame(columns=["interaction_id", "post_id", "username", "type", "content", "timestamp"]).to_csv(INTERACTIONS_CSV, index=False)

# --- Helper Functions ---

# --- Authentication Helpers ---
def hash_password(password):
    """Hashes a password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

# Note: Your existing login_signup uses plain text passwords from CSV.
# For security, you should hash passwords before saving them.
# I've modified login_signup to use the hash_password function.

def save_post(username, caption, media_file=None):
    """Saves post details to CSV and media file to storage."""
    post_id = str(uuid.uuid4())
    media_path = ""
    if media_file:
        file_extension = Path(media_file.name).suffix
        media_filename = f"{post_id}{file_extension}"
        media_path = str(STORAGE_DIR / media_filename)
        with open(media_path, "wb") as f:
            f.write(media_file.getbuffer())

    timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

    new_post = pd.DataFrame([{
        "post_id": post_id,
        "username": username,
        "timestamp": timestamp,
        "caption": caption,
        "media_path": media_path
    }])
    new_post.to_csv(POSTS_CSV, mode='a', header=False, index=False)
    st.cache_data.clear() # Clear cache for posts after saving
    return True

def record_interaction(post_id, username, interaction_type, content=""):
    """Records a like or comment in interactions.csv."""
    interaction_id = str(uuid.uuid4())
    timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

    new_interaction = pd.DataFrame([{
        "interaction_id": interaction_id,
        "post_id": post_id,
        "username": username,
        "type": interaction_type,
        "content": content,
        "timestamp": timestamp
    }])
    new_interaction.to_csv(INTERACTIONS_CSV, mode='a', header=False, index=False)
    st.cache_data.clear() # Clear cache for interactions
    return True

def remove_interaction(interaction_id):
    """Removes a specific interaction by ID from interactions.csv."""
    if not INTERACTIONS_CSV.exists() or INTERACTIONS_CSV.stat().st_size == 0:
        return False

    interactions_df = pd.read_csv(INTERACTIONS_CSV)
    original_rows = len(interactions_df)

    interactions_df = interactions_df[interactions_df['interaction_id'] != interaction_id]

    if len(interactions_df) < original_rows:
        interactions_df.to_csv(INTERACTIONS_CSV, index=False)
        st.cache_data.clear() # Clear cache for interactions
        return True
    return False

def get_post_interactions(post_id):
    """Retrieves likes and comments for a specific post."""
    if not INTERACTIONS_CSV.exists() or INTERACTIONS_CSV.stat().st_size == 0:
        return {'likes_count': 0, 'comments_df': pd.DataFrame(), 'user_like_id': None}

    # Load interactions only if the file is not empty
    interactions_df = pd.read_csv(INTERACTIONS_CSV)
    post_interactions = interactions_df[interactions_df['post_id'] == post_id]

    likes_data = post_interactions[post_interactions['type'] == 'like']
    likes_count = likes_data.shape[0]

    user_like_id = None
    if st.session_state.logged_in:
        user_like = likes_data[likes_data['username'] == st.session_state.username]
        if not user_like.empty:
            user_like_id = user_like.iloc[0]['interaction_id']

    comments_df = post_interactions[post_interactions['type'] == 'comment'].sort_values(by="timestamp", ascending=True)

    return {'likes_count': likes_count, 'comments_df': comments_df, 'user_like_id': user_like_id}

# --- NEW HELPER FUNCTION FOR DELETING POSTS ---
def remove_post(post_id):
    """Removes a post by ID from POSTS_CSV and its associated media/interactions."""
    if not POSTS_CSV.exists() or POSTS_CSV.stat().st_size == 0:
        return False

    posts_df = pd.read_csv(POSTS_CSV)
    original_posts_rows = len(posts_df)

    post_to_delete = posts_df[posts_df['post_id'] == post_id]

    if not post_to_delete.empty:
        # Delete associated media file if it exists
        media_path = post_to_delete.iloc[0]['media_path']
        if media_path and os.path.exists(media_path):
            os.remove(media_path)
            # st.info(f"మీడియా ఫైల్ తొలగించబడింది: {media_path}") # For debugging

        # Remove the post from the DataFrame
        posts_df = posts_df[posts_df['post_id'] != post_id]
        posts_df.to_csv(POSTS_CSV, index=False)
        st.cache_data.clear() # Clear cache for posts

        # Optionally, remove associated interactions as well (likes/comments)
        if INTERACTIONS_CSV.exists() and INTERACTIONS_CSV.stat().st_size > 0:
            interactions_df = pd.read_csv(INTERACTIONS_CSV)
            interactions_df = interactions_df[interactions_df['post_id'] != post_id]
            interactions_df.to_csv(INTERACTIONS_CSV, index=False)
            st.cache_data.clear() # Clear cache for interactions

        return True if len(posts_df) < original_posts_rows else False
    return False

# --- End NEW HELPER FUNCTION ---

def display_posts(filter_by_username=None): # Modified to allow filtering
    st.subheader("📢 కమ్యూనిటీ పోస్ట్‌లు") # "Community Posts"
    if not POSTS_CSV.exists() or POSTS_CSV.stat().st_size == 0:
        st.info("ఇంకా పోస్ట్‌లు లేవు! మొదట మీరే పంచుకోండి.") # "No posts yet! Be the first to share something."
        return

    posts_df = pd.read_csv(POSTS_CSV).sort_values(by="timestamp", ascending=False)

    if filter_by_username:
        posts_df = posts_df[posts_df['username'] == filter_by_username]
        st.subheader(f"@{filter_by_username} యొక్క పోస్ట్‌లు")
        if posts_df.empty:
            st.info(f"@{filter_by_username} ఇంకా పోస్ట్‌లు చేయలేదు.")
            return

    if posts_df.empty:
        st.info("ఇంకా పోస్ట్‌లు లేవు! మొదట మీరే పంచుకోండి.") # "No posts yet! Be the first to share something."
        return

    interaction_key_counter = 0

    for index, post in posts_df.iterrows():
        # --- Display Post Header ---
        post_col1, post_col2 = st.columns([3, 1]) # Columns for post content and delete button
        with post_col1:
            st.markdown(f"**@{post['username']}** <small>_{post['timestamp']}_</small>")
            st.write(post['caption'])
        with post_col2:
            # Only show delete button if current logged-in user is the author
            if st.session_state.logged_in and st.session_state.username == post['username']:
                delete_button_key = f"delete_post_{post['post_id']}_{interaction_key_counter}"
                if st.button("తొలగించు", key=delete_button_key): # "Delete" button
                    if st.session_state.get(f'confirm_delete_{post["post_id"]}', False):
                        if remove_post(post['post_id']):
                            st.success(f"'{post['caption'][:30]}...' పోస్ట్ విజయవంతంగా తొలగించబడింది!")
                            if f'confirm_delete_{post["post_id"]}' in st.session_state:
                                del st.session_state[f'confirm_delete_{post["post_id"]}']
                            st.rerun() # Rerun to refresh the list
                        else:
                            st.error("పోస్ట్‌ను తొలగించడంలో లోపం.")
                    else:
                        st.warning(f"మీరు నిజంగా '{post['caption'][:30]}...' పోస్ట్‌ను తొలగించాలనుకుంటున్నారా?")
                        st.session_state[f'confirm_delete_{post["post_id"]}'] = True
                        st.button("తొలగింపును నిర్ధారించండి", key=f"confirm_delete_btn_{post['post_id']}_{interaction_key_counter}")

        # --- Display Media (if any) ---
        if post['media_path'] and os.path.exists(post['media_path']):
            file_extension = Path(post['media_path']).suffix.lower()
            if file_extension in [".png", ".jpg", ".jpeg", ".gif"]:
                st.image(post['media_path'], use_container_width=True, caption=f"@{post['username']} ద్వారా పోస్ట్ చేయబడింది")
            elif file_extension in [".mp4", ".mov", ".avi", ".webm"]:
                st.video(post['media_path'])
            else:
                st.warning(f"ఈ మీడియా రకం మద్దతు లేదు: {post['media_path']}. ఫైల్ మార్గం చూపుతోంది.")
                st.write(post['media_path'])

        # --- Like, Comment, Share Section ---
        interactions_data = get_post_interactions(post['post_id'])
        current_likes_count = interactions_data['likes_count']
        current_comments_df = interactions_data['comments_df']
        user_like_id = interactions_data['user_like_id']

        interaction_key_counter += 1
        like_button_key = f"like_{post['post_id']}_{interaction_key_counter}"
        comment_button_key = f"comment_submit_{post['post_id']}_{interaction_key_counter}"
        comment_input_key = f"comment_input_{post['post_id']}_{interaction_key_counter}"
        share_button_key = f"share_{post['post_id']}_{interaction_key_counter}"


        col_like, col_comment_btn, col_share = st.columns([1, 1, 1])

        with col_like:
            if st.session_state.logged_in: # Only show like/unlike if logged in
                if user_like_id:
                    like_label = f"❤️ ఇష్టం లేదు ({current_likes_count})" # "Unlike"
                    if st.button(like_label, key=like_button_key, help="ఈ పోస్ట్‌ను ఇష్టం తీసివేయండి"):
                        if remove_interaction(user_like_id):
                            st.success("ఇష్టం తీసివేయబడింది!") # "Unlike successful!"
                            st.rerun()
                        else:
                            st.error("ఇష్టం తీసివేయడంలో లోపం.") # "Error unliking."
                else:
                    like_label = f"👍 ఇష్టం ({current_likes_count})" # "Like"
                    if st.button(like_label, key=like_button_key, help="ఈ పోస్ట్‌ను ఇష్టపడండి"):
                        record_interaction(post['post_id'], st.session_state.username, 'like')
                        st.success("పోస్ట్ ఇష్టపడబడింది!")
                        st.rerun()
            else:
                st.info(f"ఇష్టాలు: {current_likes_count} (లాగిన్ చేయండి)") # Display like count but disable interaction if not logged in

        with col_comment_btn:
            # Changed to a button that indicates comments are viewable/addable,
            # disabled if not logged in
            if st.session_state.logged_in:
                st.button(f"💬 వ్యాఖ్యలు ({current_comments_df.shape[0]})", key=f"view_comments_{post['post_id']}_{interaction_key_counter}")
            else:
                 st.info(f"వ్యాఖ్యలు: {current_comments_df.shape[0]} (లాగిన్ చేయండి)")


        with col_share:
            if st.button("🔗 భాగస్వామ్యం", key=share_button_key, help="ఈ పోస్ట్‌ను భాగస్వామ్యం చేయండి"):
                st.info("భాగస్వామ్య ఎంపికలు త్వరలో వస్తాయి!")

        # Show Expander for comments only if logged in OR if there are existing comments
        if st.session_state.logged_in or not current_comments_df.empty:
            with st.expander(f"వ్యాఖ్యలను జోడించండి/చూడండి ({current_comments_df.shape[0]})"):
                if st.session_state.logged_in: # Allow adding comment only if logged in
                    new_comment = st.text_input("మీ వ్యాఖ్యను వ్రాయండి...", key=comment_input_key)
                    if st.button("వ్యాఖ్యను సమర్పించండి", key=comment_button_key):
                        if new_comment.strip():
                            record_interaction(post['post_id'], st.session_state.username, 'comment', new_comment.strip())
                            st.success("మీ వ్యాఖ్య భాగస్వామ్యం చేయబడింది!")
                            st.rerun()
                        else:
                            st.warning("దయచేసి వ్యాఖ్యను వ్రాయండి.")
                else:
                    st.info("వ్యాఖ్యానించడానికి లాగిన్ చేయండి.") # Prompt to log in to comment

                st.markdown("##### వ్యాఖ్యలు:")
                if current_comments_df.empty:
                    st.info("ఇంకా వ్యాఖ్యలు లేవు. మొదట వ్యాఖ్యానించండి!")
                else:
                    for idx, comment in current_comments_df.iterrows():
                        st.markdown(f"**@{comment['username']}** <small>_{comment['timestamp']}_</small>")
                        st.write(f"&nbsp;&nbsp;&nbsp;&nbsp;{comment['content']}")

        st.markdown("---")

# --- Custom CSS for a professional touch ---
st.markdown(
    """
    <style>
    body {
        font-family: 'NATS', 'Telugu', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol";
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: "Baloo Tammudu 2", 'Telugu', sans-serif;
        color: #2e7d32;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        padding: 10px 24px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 8px;
        border: none;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    /* For the Unlike button specifically to change color */
    /* This targets the button that has a red heart and is the 'Unlike' button */
    /* Note: Streamlit doesn't directly expose a way to style based on content,
       so this is a best effort based on potential internal data-testid or structure.
       If you want a truly distinct 'Unlike' button style, you might need custom JS. */
    .stButton>button:has(span:contains("❤️")) {
        background-color: #d33; /* Red color for Unlike */
    }
    .stButton>button:has(span:contains("❤️")):hover {
        background-color: #c00;
    }

    .stRadio > label {
        font-size: 1.1em;
        font-weight: bold;
        color: #1a5e20;
    }
    .st-emotion-cache-16txt4v p, .st-emotion-cache-16txt4v div, .st-emotion-cache-16txt4v span {
        font-size: 1.05em;
        line-height: 1.6;
    }
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)

# --- Authentication ---
# Moved this section to be closer to where it's used and modified it for hashed passwords
# Note: In your original, you were reading plain text passwords.
# I've updated the logic to hash passwords during signup and verify during login.

# --- User Authentication Helper Functions (Moved here for better organization) ---
@st.cache_data
def load_users():
    """Loads user data from the CSV file."""
    if not USER_CSV.exists() or USER_CSV.stat().st_size == 0:
        return pd.DataFrame(columns=["username", "password", "email", "about", "dob"])
    return pd.read_csv(USER_CSV)

def save_users(df):
    """Saves user data to the CSV file."""
    df.to_csv(USER_CSV, index=False)
    st.cache_data.clear() # Clear cache to ensure fresh data on next load

# --- Authentication Login/Signup ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'login_status_message' not in st.session_state:
    st.session_state.login_status_message = ""
if 'auth_view' not in st.session_state:
    st.session_state.auth_view = "login" # 'login' or 'signup'

def login_signup():
    st.subheader("🔑 లాగిన్ / సైన్ అప్")

    if st.session_state.login_status_message:
        if "విజయవంతంగా" in st.session_state.login_status_message or "స్వాగతం" in st.session_state.login_status_message:
            st.success(st.session_state.login_status_message)
        elif "తప్పు" in st.session_state.login_status_message or "సరిపోలడం లేదు" in st.session_state.login_status_message or "ఇప్పటికే ఉంది" in st.session_state.login_status_message:
            st.error(st.session_state.login_status_message)
        else:
            st.warning(st.session_state.login_status_message)
        st.session_state.login_status_message = "" # Clear message after display

    auth_options = ["లాగిన్", "సైన్ అప్"]
    selected_auth_option = st.radio(
        "ఎంచుకోండి:", # "Select:"
        auth_options,
        index=0 if st.session_state.auth_view == "login" else 1,
        key="auth_selector",
        horizontal=True
    )

    if selected_auth_option == "లాగిన్":
        st.session_state.auth_view = "login"
    else:
        st.session_state.auth_view = "signup"

    if st.session_state.auth_view == "login":
        st.markdown("#### ప్రస్తుత వినియోగదారు లాగిన్")
        login_username = st.text_input("వినియోగదారు పేరు (లాగిన్)", key="login_username_form")
        login_password = st.text_input("పాస్‌వర్డ్ (లాగిన్)", type="password", key="login_password_form")
        if st.button("లాగిన్", key="do_login_button"):
            users_df = load_users()
            # Verify hashed password
            user_found = users_df[(users_df['username'] == login_username) & (users_df['password'] == hash_password(login_password))]
            if not user_found.empty:
                st.session_state.logged_in = True
                st.session_state.username = login_username
                st.session_state.login_status_message = f"స్వాగతం, {login_username}!"
            else:
                st.session_state.login_status_message = "తప్పు వినియోగదారు పేరు లేదా పాస్‌వర్డ్."
            st.rerun()

    elif st.session_state.auth_view == "signup":
        st.markdown("#### కొత్త వినియోగదారు సైన్ అప్")
        signup_username = st.text_input("వినియోగదారు పేరు (సైన్ అప్)", key="signup_username_form")
        signup_password = st.text_input("పాస్‌వర్డ్ (సైన్ అప్)", type="password", key="signup_password_form")
        signup_confirm_password = st.text_input("పాస్‌వర్డ్ నిర్ధారించండి", type="password", key="signup_confirm_password_form")
        if st.button("సైన్ అప్", key="do_signup_button"):
            if not signup_username or not signup_password or not signup_confirm_password:
                st.session_state.login_status_message = "దయచేసి అన్ని సైన్-అప్ ఫీల్డ్‌లను పూరించండి."
            elif signup_password != signup_confirm_password:
                st.session_state.login_status_message = "పాస్‌వర్డ్‌లు సరిపోలడం లేదు."
            else:
                users_df = load_users()
                if signup_username in users_df['username'].values:
                    st.session_state.login_status_message = "వినియోగదారు పేరు ఇప్పటికే ఉంది. దయచేసి మరొకటి ఎంచుకోండి."
                else:
                    new_user = pd.DataFrame([{"username": signup_username, "password": hash_password(signup_password), "email": "", "about": "", "dob": ""}]) # Hash pas
