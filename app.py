import streamlit as st
import pandas as pd
import os
import time
import uuid
from pathlib import Path

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
INTERACTIONS_CSV = STORAGE_DIR / "interactions.csv" # New CSV for likes/comments

STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Initialize users.csv - ADD 'about' and 'dob' columns
if not USER_CSV.exists():
    pd.DataFrame(columns=["username", "password", "email", "about", "dob"]).to_csv(USER_CSV, index=False)
else:
    # Ensure existing users.csv has 'about' and 'dob' columns
    users_df_check = pd.read_csv(USER_CSV)
    if 'about' not in users_df_check.columns:
        users_df_check['about'] = ''
        users_df_check.to_csv(USER_CSV, index=False)
    if 'dob' not in users_df_check.columns:
        users_df_check['dob'] = ''
        users_df_check.to_csv(USER_CSV, index=False)


if not POSTS_CSV.exists():
    pd.DataFrame(columns=["post_id", "username", "timestamp", "caption", "media_path"]).to_csv(POSTS_CSV, index=False)

# Initialize interactions.csv
if not INTERACTIONS_CSV.exists():
    pd.DataFrame(columns=["interaction_id", "post_id", "username", "type", "content", "timestamp"]).to_csv(INTERACTIONS_CSV, index=False)

# --- Helper Functions ---

def save_post(username, caption, media_file=None):
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
    return True

def get_post_interactions(post_id):
    """Retrieves likes and comments for a specific post."""
    if not INTERACTIONS_CSV.exists() or INTERACTIONS_CSV.stat().st_size == 0:
        return {'likes': 0, 'comments': pd.DataFrame()}

    interactions_df = pd.read_csv(INTERACTIONS_CSV)
    post_interactions = interactions_df[interactions_df['post_id'] == post_id]
    
    likes = post_interactions[post_interactions['type'] == 'like'].shape[0]
    comments = post_interactions[post_interactions['type'] == 'comment'].sort_values(by="timestamp", ascending=True) # Show oldest comments first

    return {'likes': likes, 'comments': comments}

def display_posts():
    st.subheader("📢 కమ్యూనిటీ పోస్ట్‌లు") # "Community Posts"
    if not POSTS_CSV.exists() or POSTS_CSV.stat().st_size == 0:
        st.info("ఇంకా పోస్ట్‌లు లేవు! మొదట మీరే పంచుకోండి.") # "No posts yet! Be the first to share something."
        return

    posts_df = pd.read_csv(POSTS_CSV).sort_values(by="timestamp", ascending=False)

    if posts_df.empty:
        st.info("ఇంకా పోస్ట్‌లు లేవు! మొదట మీరే పంచుకోండి.") # "No posts yet! Be the first to share something."
        return

    # To ensure comments/likes update, we need a unique key for each post interaction section
    # Use a counter for unique keys across dynamically generated content
    interaction_key_counter = 0

    for index, post in posts_df.iterrows():
        st.markdown(f"**@{post['username']}** <small>_{post['timestamp']}_</small>")
        st.write(post['caption'])
        if post['media_path'] and os.path.exists(post['media_path']):
            file_extension = Path(post['media_path']).suffix.lower()
            if file_extension in [".png", ".jpg", ".jpeg", ".gif"]:
                st.image(post['media_path'], use_container_width=True, caption=f"@{post['username']} ద్వారా పోస్ట్ చేయబడింది")
            elif file_extension in [".mp4", ".mov", ".avi", ".webm"]:
                st.video(post['media_path'])
            else:
                st.warning(f"ఈ మీడియా రకం మద్దతు లేదు {post['media_path']}. ఫైల్ మార్గం చూపుతోంది.")
                st.write(post['media_path'])

        # --- Like, Comment, Share Section ---
        interactions = get_post_interactions(post['post_id'])
        current_likes = interactions['likes']
        current_comments_df = interactions['comments']

        # Ensure unique keys for buttons within the loop
        interaction_key_counter += 1
        like_button_key = f"like_{post['post_id']}_{interaction_key_counter}"
        comment_button_key = f"comment_submit_{post['post_id']}_{interaction_key_counter}"
        comment_input_key = f"comment_input_{post['post_id']}_{interaction_key_counter}"
        share_button_key = f"share_{post['post_id']}_{interaction_key_counter}"


        col_like, col_comment_btn, col_share = st.columns([1, 1, 1])

        with col_like:
            # Check if current user already liked this post
            user_has_liked = False
            if not current_comments_df.empty: # comments_df actually holds all interactions for the post
                user_likes = current_comments_df[(current_comments_df['type'] == 'like') & (current_comments_df['username'] == st.session_state.username)]
                if not user_likes.empty:
                    user_has_liked = True

            like_label = f"👍 ఇష్టం ({current_likes})" if not user_has_liked else f"✅ ఇష్టం ({current_likes})"
            if st.button(like_label, key=like_button_key, help="ఈ పోస్ట్‌ను ఇష్టపడండి"):
                if not user_has_liked:
                    record_interaction(post['post_id'], st.session_state.username, 'like')
                    st.success("పోస్ట్ ఇష్టపడబడింది!") # "Post liked!"
                    st.rerun() # Rerun to update like count immediately
                else:
                    st.info("మీరు ఇప్పటికే ఈ పోస్ట్‌ను ఇష్టపడ్డారు.") # "You have already liked this post."

        with col_comment_btn:
            st.button(f"💬 వ్యాఖ్యలు ({current_comments_df[current_comments_df['type'] == 'comment'].shape[0]})", key=f"view_comments_{post['post_id']}_{interaction_key_counter}", disabled=True) # Just a count button

        with col_share:
            if st.button("🔗 భాగస్వామ్యం", key=share_button_key, help="ఈ పోస్ట్‌ను భాగస్వామ్యం చేయండి"):
                st.info("భాగస్వామ్య ఎంపికలు త్వరలో వస్తాయి!") # "Share options coming soon!"
                # In a real app, you might show a text input with the post URL or invoke browser share API

        # Comment Input Section
        with st.expander(f"వ్యాఖ్యలను జోడించండి/చూడండి ({current_comments_df[current_comments_df['type'] == 'comment'].shape[0]})"):
            new_comment = st.text_input("మీ వ్యాఖ్యను వ్రాయండి...", key=comment_input_key) # "Write your comment..."
            if st.button("వ్యాఖ్యను సమర్పించండి", key=comment_button_key): # "Submit Comment"
                if new_comment.strip():
                    record_interaction(post['post_id'], st.session_state.username, 'comment', new_comment.strip())
                    st.success("మీ వ్యాఖ్య భాగస్వామ్యం చేయబడింది!") # "Your comment has been shared!"
                    st.rerun() # Rerun to show the new comment immediately
                else:
                    st.warning("దయచేసి వ్యాఖ్యను వ్రాయండి.") # "Please write a comment."

            st.markdown("##### వ్యాఖ్యలు:") # "Comments:"
            if current_comments_df[current_comments_df['type'] == 'comment'].empty:
                st.info("ఇంకా వ్యాఖ్యలు లేవు. మొదట వ్యాఖ్యానించండి!") # "No comments yet. Be the first to comment!"
            else:
                for idx, comment in current_comments_df[current_comments_df['type'] == 'comment'].iterrows():
                    st.markdown(f"**@{comment['username']}** <small>_{comment['timestamp']}_</small>")
                    st.write(f"&nbsp;&nbsp;&nbsp;&nbsp;{comment['content']}") # Indent comments for readability
                
        st.markdown("---") # Separator between posts

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
    .stRadio > label {
        font-size: 1.1em;
        font-weight: bold;
        color: #1a5e20;
    }
    /* Adjusted text for better Telugu readability */
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
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'login_status_message' not in st.session_state:
    st.session_state.login_status_message = ""

def login_signup():
    st.subheader("🔑 లాగిన్ / సైన్ అప్")

    if st.session_state.login_status_message:
        if "విజయవంతంగా" in st.session_state.login_status_message or "స్వాగతం" in st.session_state.login_status_message:
            st.success(st.session_state.login_status_message)
        elif "తప్పు" in st.session_state.login_status_message or "సరిపోలడం లేదు" in st.session_state.login_status_message or "ఇప్పటికే ఉంది" in st.session_state.login_status_message:
            st.error(st.session_state.login_status_message)
        else:
            st.warning(st.session_state.login_status_message)
        st.session_state.login_status_message = ""

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### ప్రస్తుత వినియోగదారు లాగిన్")
        login_username = st.text_input("వినియోగదారు పేరు (లాగిన్)", key="login_username")
        login_password = st.text_input("పాస్‌వర్డ్ (లాగిన్)", type="password", key="login_password")
        if st.button("లాగిన్"):
            users_df = pd.read_csv(USER_CSV)
            user_found = users_df[(users_df['username'] == login_username) & (users_df['password'] == login_password)]
            if not user_found.empty:
                st.session_state.logged_in = True
                st.session_state.username = login_username
                st.session_state.login_status_message = f"స్వాగతం, {login_username}!"
            else:
                st.session_state.login_status_message = "తప్పు వినియోగదారు పేరు లేదా పాస్‌వర్డ్."


    with col2:
        st.markdown("#### కొత్త వినియోగదారు సైన్ అప్")
        signup_username = st.text_input("వినియోగదారు పేరు (సైన్ అప్)", key="signup_username")
        signup_password = st.text_input("పాస్‌వర్డ్ (సైన్ అప్)", type="password", key="signup_password")
        signup_confirm_password = st.text_input("పాస్‌వర్డ్ నిర్ధారించండి", type="password", key="signup_confirm_password")
        if st.button("సైన్ అప్"):
            if not signup_username or not signup_password or not signup_confirm_password:
                st.session_state.login_status_message = "దయచేసి అన్ని సైన్-అప్ ఫీల్డ్‌లను పూరించండి."
            elif signup_password != signup_confirm_password:
                st.session_state.login_status_message = "పాస్‌వర్డ్‌లు సరిపోలడం లేదు."
            else:
                users_df = pd.read_csv(USER_CSV)
                if signup_username in users_df['username'].values:
                    st.session_state.login_status_message = "వినియోగదారు పేరు ఇప్పటికే ఉంది. దయచేసి మరొకటి ఎంచుకోండి."
                else:
                    new_user = pd.DataFrame([{"username": signup_username, "password": signup_password, "email": "", "about": "", "dob": ""}])
                    new_user.to_csv(USER_CSV, mode='a', header=False, index=False)
                    st.session_state.login_status_message = "ఖాతా విజయవంతంగా సృష్టించబడింది! మీరు ఇప్పుడు లాగిన్ చేయవచ్చు."

# --- Main App Logic ---
if not st.session_state.logged_in:
    login_signup()
else:
    st.sidebar.title(f"స్వాగతం, {st.session_state.username}!")
    st.sidebar.radio(
        "నావిగేషన్",
        ("🏠 హోమ్", "📝 పోస్ట్", "👤 ప్రొఫైల్"),
        key="navigation_radio",
        help="పేజీని నావిగేట్ చేయడానికి ఎంచుకోండి."
    )

    page = st.session_state.navigation_radio

    if page == "🏠 హోమ్":
        display_posts()

    elif page == "📝 పోస్ట్":
        st.subheader("✏️ కొత్త పోస్ట్ సృష్టించండి")

        with st.form(key="new_post", clear_on_submit=True):
            col_caption, col_media = st.columns([2, 1])

            with col_caption:
                caption = st.text_area(
                    "ఏం జరుగుతోంది?",
                    height=150,
                    max_chars=500,
                    help="మీ ఆలోచనలు, భావాలు లేదా వార్తలను పంచుకోండి (గరిష్టంగా 500 అక్షరాలు)."
                )
                if caption:
                    char_count = len(caption)
                    if char_count > 450:
                        st.warning(f"అక్షరాలు: {char_count}/500 - పరిమితికి దగ్గరగా ఉంది!")
                    else:
                        st.info(f"అక్షరాలు: {char_count}/500")

            with col_media:
                st.markdown("---")
                media_file = st.file_uploader(
                    "చిత్రం/వీడియోను అప్‌లోడ్ చేయండి",
                    type=["png", "jpg", "jpeg", "gif", "mp4", "mov", "avi", "webm"],
                    help="మద్దతు ఉన్న ఫార్మాట్‌లు: PNG, JPG, JPEG, GIF, MP4, MOV, AVI, WEBM. గరిష్టంగా 5MB సిఫార్సు చేయబడింది."
                )
                if media_file is not None:
                    file_size_mb = round(media_file.size / (1024 * 1024), 2)
                    st.success(f"ఫైల్ ఎంచుకోబడింది: {media_file.name} ({file_size_mb} MB)")
                    if "image" in media_file.type:
                        st.image(media_file, caption="చిత్ర ప్రివ్యూ", width=150)
                    elif "video" in media_file.type:
                        st.video(media_file)
                    else:
                        st.info("ఫైల్ అప్‌లోడ్ చేయబడింది, కానీ ఈ రకానికి ప్రివ్యూ అందుబాటులో లేదు.")

            submitted = st.form_submit_button("పోస్ట్ చేయండి")

            if submitted:
                if not caption.strip() and not media_file:
                    st.error("🚫 దయచేసి శీర్షికను జోడించండి లేదా భాగస్వామ్యం చేయడానికి చిత్రం/వీడియోను అప్‌లోడ్ చేయండి.")
                elif not caption.strip():
                    st.error("🚫 మీ పోస్ట్‌కు శీర్షిక అవసరం.")
                elif media_file and media_file.size > 5 * 1024 * 1024:
                    st.error("🚫 మీడియా ఫైల్ చాలా పెద్దది. దయచేసి 5MB కంటే తక్కువ ఫైల్‌లను అప్‌లోడ్ చేయండి.")
                else:
                    with st.spinner("🚀 మీ కంటెంట్‌ను పోస్ట్ చేస్తోంది... దయచేసి వేచి ఉండండి."):
                        time.sleep(1)
                        success = save_post(st.session_state.username, caption, media_file)

                    if success:
                        st.success("✅ మీ పోస్ట్ విజయవంతంగా భాగస్వామ్యం చేయబడింది!")
                        st.balloons()
                    else:
                        st.error("మీ పోస్ట్‌ను సేవ్ చేయడంలో ఏదో తప్పు జరిగింది. దయచేసి మళ్లీ ప్రయత్నించండి.")

    elif page == "👤 ప్రొఫైల్":
        st.subheader(f"👤 {st.session_state.username} యొక్క ప్రొఫైల్")

        users_df = pd.read_csv(USER_CSV)
        current_user_data = users_df[users_df['username'] == st.session_state.username].iloc[0]

        st.write(f"**వినియోగదారు పేరు:** {st.session_state.username}")

        # Profile editing form
        st.markdown("---")
        st.markdown("#### ప్రొఫైల్ వివరాలను సవరించండి") # "Edit Profile Details"
        with st.form(key="edit_profile_form"):
            current_about = current_user_data.get('about', '')
            current_dob = current_user_data.get('dob', '')

            new_about = st.text_area("నా గురించి (About Me)", value=current_about, height=100)
            new_dob = st.text_input("పుట్టిన తేదీ (YYYY-MM-DD)", value=current_dob, help="ఉదా: 1990-01-15")

            save_profile_button = st.form_submit_button("ప్రొఫైల్‌ను సేవ్ చేయండి")

            if save_profile_button:
                users_df.loc[users_df['username'] == st.session_state.username, 'about'] = new_about
                users_df.loc[users_df['username'] == st.session_state.username, 'dob'] = new_dob
                users_df.to_csv(USER_CSV, index=False)
                st.success("✅ ప్రొఫైల్ విజయవంతంగా నవీకరించబడింది!")

        st.markdown("---")
        st.markdown("#### మీ ప్రొఫైల్ వివరాలు")
        st.write(f"**నా గురించి:** {current_user_data.get('about', 'ఇంకా వివరాలు లేవు.')}")
        st.write(f"**పుట్టిన తేదీ:** {current_user_data.get('dob', 'ఇంకా వివరాలు లేవు.')}")


        st.markdown("---")
        st.markdown("#### మీ ఇటీవలి పోస్ట్‌లు")
        if not POSTS_CSV.exists() or POSTS_CSV.stat().st_size == 0:
            st.info("మీరు ఇంకా ఏ పోస్ట్‌లు చేయలేదు.")
        else:
            posts_df = pd.read_csv(POSTS_CSV)
            user_posts = posts_df[posts_df['username'] == st.session_state.username].sort_values(by="timestamp", ascending=False)
            if user_posts.empty:
                st.info("మీరు ఇంకా ఏ పోస్ట్‌లు చేయలేదు.")
            else:
                for index, post in user_posts.iterrows():
                    st.markdown(f"**<small>_{post['timestamp']}_</small>**")
                    st.write(post['caption'])
                    if post['media_path'] and os.path.exists(post['media_path']):
                        file_extension = Path(post['media_path']).suffix.lower()
                        if file_extension in [".png", ".jpg", ".jpeg", ".gif"]:
                            st.image(post['media_path'], use_container_width=True)
                        elif file_extension in [".mp4", ".mov", ".avi", ".webm"]:
                            st.video(post['media_path'])
                        else:
                            st.warning(f"ఈ మీడియా రకం మద్దతు లేదు {post['media_path']}. ఫైల్ మార్గం చూపుతోంది.")
                            st.write(post['media_path'])
                    st.markdown("---")


    st.sidebar.markdown("---")
    if st.sidebar.button("లాగ్ అవుట్", help="మీ ఖాతా నుండి లాగ్ అవుట్ చేయడానికి క్లిక్ చేయండి."):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.login_status_message = "మీరు లాగ్ అవుట్ అయ్యారు."        
