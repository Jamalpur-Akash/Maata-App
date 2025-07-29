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
INTERACTIONS_CSV = STORAGE_DIR / "interactions.csv"

STORAGE_DIR.mkdir(parents=True, exist_ok=True)

if not USER_CSV.exists():
    pd.DataFrame(columns=["username", "password", "email", "about", "dob"]).to_csv(USER_CSV, index=False)
else:
    users_df_check = pd.read_csv(USER_CSV)
    if 'about' not in users_df_check.columns:
        users_df_check['about'] = ''
        users_df_check.to_csv(USER_CSV, index=False)
    if 'dob' not in users_df_check.columns:
        users_df_check['dob'] = ''
        users_df_check.to_csv(USER_CSV, index=False)

if not POSTS_CSV.exists():
    pd.DataFrame(columns=["post_id", "username", "timestamp", "caption", "media_path"]).to_csv(POSTS_CSV, index=False)

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

def remove_interaction(interaction_id):
    """Removes a specific interaction by ID from interactions.csv."""
    if not INTERACTIONS_CSV.exists() or INTERACTIONS_CSV.stat().st_size == 0:
        return False
    
    interactions_df = pd.read_csv(INTERACTIONS_CSV)
    original_rows = len(interactions_df)
    
    # Filter out the interaction to be removed
    interactions_df = interactions_df[interactions_df['interaction_id'] != interaction_id]
    
    if len(interactions_df) < original_rows: # Check if something was actually removed
        interactions_df.to_csv(INTERACTIONS_CSV, index=False)
        return True
    return False

def get_post_interactions(post_id):
    """Retrieves likes and comments for a specific post."""
    if not INTERACTIONS_CSV.exists() or INTERACTIONS_CSV.stat().st_size == 0:
        return {'likes_count': 0, 'comments_df': pd.DataFrame(), 'user_like_id': None}

    interactions_df = pd.read_csv(INTERACTIONS_CSV)
    post_interactions = interactions_df[interactions_df['post_id'] == post_id]
    
    likes_data = post_interactions[post_interactions['type'] == 'like']
    likes_count = likes_data.shape[0]

    user_like_id = None
    if st.session_state.logged_in: # Only check if user is logged in
        user_like = likes_data[likes_data['username'] == st.session_state.username]
        if not user_like.empty:
            user_like_id = user_like.iloc[0]['interaction_id'] # Get the ID of the user's like

    comments_df = post_interactions[post_interactions['type'] == 'comment'].sort_values(by="timestamp", ascending=True)

    return {'likes_count': likes_count, 'comments_df': comments_df, 'user_like_id': user_like_id}

def display_posts():
    st.subheader("📢 కమ్యూనిటీ పోస్ట్‌లు")
    if not POSTS_CSV.exists() or POSTS_CSV.stat().st_size == 0:
        st.info("ఇంకా పోస్ట్‌లు లేవు! మొదట మీరే పంచుకోండి.")
        return

    posts_df = pd.read_csv(POSTS_CSV).sort_values(by="timestamp", ascending=False)

    if posts_df.empty:
        st.info("ఇంకా పోస్ట్‌లు లేవు! మొదట మీరే పంచుకోండి.")
        return

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
        interactions_data = get_post_interactions(post['post_id'])
        current_likes_count = interactions_data['likes_count']
        current_comments_df = interactions_data['comments_df']
        user_like_id = interactions_data['user_like_id'] # ID of the current user's like, if any

        interaction_key_counter += 1
        like_button_key = f"like_{post['post_id']}_{interaction_key_counter}"
        comment_button_key = f"comment_submit_{post['post_id']}_{interaction_key_counter}"
        comment_input_key = f"comment_input_{post['post_id']}_{interaction_key_counter}"
        share_button_key = f"share_{post['post_id']}_{interaction_key_counter}"

        col_like, col_comment_btn, col_share = st.columns([1, 1, 1])

        with col_like:
            if user_like_id: # User has liked
                like_label = f"❤️ ఇష్టం లేదు ({current_likes_count})" # "Unlike"
                if st.button(like_label, key=like_button_key, help="ఈ పోస్ట్‌ను ఇష్టం తీసివేయండి"):
                    if remove_interaction(user_like_id):
                        st.success("ఇష్టం తీసివేయబడింది!") # "Unlike successful!"
                        st.rerun() # Rerun to update like count immediately
                    else:
                        st.error("ఇష్టం తీసివేయడంలో లోపం.") # "Error unliking."
            else: # User has not liked
                like_label = f"👍 ఇష్టం ({current_likes_count})" # "Like"
                if st.button(like_label, key=like_button_key, help="ఈ పోస్ట్‌ను ఇష్టపడండి"):
                    record_interaction(post['post_id'], st.session_state.username, 'like')
                    st.success("పోస్ట్ ఇష్టపడబడింది!")
                    st.rerun()

        with col_comment_btn:
            st.button(f"💬 వ్యాఖ్యలు ({current_comments_df.shape[0]})", key=f"view_comments_{post['post_id']}_{interaction_key_counter}", disabled=True)

        with col_share:
            if st.button("🔗 భాగస్వామ్యం", key=share_button_key, help="ఈ పోస్ట్‌ను భాగస్వామ్యం చేయండి"):
                st.info("భాగస్వామ్య ఎంపికలు త్వరలో వస్తాయి!")

        with st.expander(f"వ్యాఖ్యలను జోడించండి/చూడండి ({current_comments_df.shape[0]})"):
            new_comment = st.text_input("మీ వ్యాఖ్యను వ్రాయండి...", key=comment_input_key)
            if st.button("వ్యాఖ్యను సమర్పించండి", key=comment_button_key):
                if new_comment.strip():
                    record_interaction(post['post_id'], st.session_state.username, 'comment', new_comment.strip())
                    st.success("మీ వ్యాఖ్య భాగస్వామ్యం చేయబడింది!")
                    st.rerun()
                else:
                    st.warning("దయచేసి వ్యాఖ్యను వ్రాయండి.")

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
    .stButton>button[data-testid*="stButton-primary"] { /* Targeting the primary style if applied */
        background-color: #d33; /* Red color for Unlike */
    }
    .stButton>button[data-testid*="stButton-primary"]:hover {
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
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'login_status_message' not in st.session_state:
    st.session_state.login_status_message = ""
if 'auth_view' not in st.session_state:
    st.session_state.auth_view = "login"

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

    auth_options = ["లాగిన్", "సైన్ అప్"]
    selected_auth_option = st.radio(
        "ఎంచుకోండి:",
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
            users_df = pd.read_csv(USER_CSV)
            user_found = users_df[(users_df['username'] == login_username) & (users_df['password'] == login_password)]
            if not user_found.empty:
                st.session_state.logged_in = True
                st.session_state.username = login_username
                st.session_state.login_status_message = f"స్వాగతం, {login_username}!"
            else:
                st.session_state.login_status_message = "తప్పు వినియోగదారు పేరు లేదా పాస్‌వర్డ్."

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
                users_df = pd.read_csv(USER_CSV)
                if signup_username in users_df['username'].values:
                    st.session_state.login_status_message = "వినియోగదారు పేరు ఇప్పటికే ఉంది. దయచేసి మరొకటి ఎంచుకోండి."
                else:
                    new_user = pd.DataFrame([{"username": signup_username, "password": signup_password, "email": "", "about": "", "dob": ""}])
                    new_user.to_csv(USER_CSV, mode='a', header=False, index=False)
                    st.session_state.login_status_message = "ఖాతా విజయవంతంగా సృష్టించబడింది! మీరు ఇప్పుడు లాగిన్ చేయవచ్చు."
                    st.session_state.auth_view = "login"


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
                st.markdown("##### పోస్ట్ శీర్షిక")
                pasted_text = st.text_input(
                    "క్లిప్‌బోర్డ్ నుండి ఇక్కడ పేస్ట్ చేయండి (Ctrl+V/Cmd+V)",
                    key="clipboard_paste_input"
                )
                if st.button("శీర్షికకు కాపీ చేయండి", key="copy_to_caption"):
                    if pasted_text:
                        st.session_state.current_caption_value = pasted_text
                        st.info("క్లిప్‌బోర్డ్ నుండి శీర్షికకు కాపీ చేయబడింది.")
                    else:
                        st.warning("పేస్ట్ చేయడానికి టెక్స్ట్ బాక్స్ ఖాళీగా ఉంది.")

                if 'current_caption_value' not in st.session_state:
                    st.session_state.current_caption_value = ""

                caption = st.text_area(
                    "ఏం జరుగుతోంది?",
                    value=st.session_state.current_caption_value,
                    height=150,
                    max_chars=500,
                    help="మీ ఆలోచనలు, భావాలు లేదా వార్తలను పంచుకోండి (గరిష్టంగా 500 అక్షరాలు)."
                )
                if caption != st.session_state.current_caption_value:
                    st.session_state.current_caption_value = caption

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
                st.session_state.current_caption_value = ""
                st.session_state.clipboard_paste_input = ""

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
                        st.rerun()
                    else:
                        st.error("మీ పోస్ట్‌ను సేవ్ చేయడంలో ఏదో తప్పు జరిగింది. దయచేసి మళ్లీ ప్రయత్నించండి.")

    elif page == "👤 ప్రొఫైల్":
        st.subheader(f"👤 {st.session_state.username} యొక్క ప్రొఫైల్")

        users_df = pd.read_csv(USER_CSV)
        current_user_data = users_df[users_df['username'] == st.session_state.username].iloc[0]

        st.write(f"**వినియోగదారు పేరు:** {st.session_state.username}")

        # Profile editing form
        st.markdown("---")
        st.markdown("#### ప్రొఫైల్ వివరాలను సవరించండి")
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
                st.rerun()

        st.markdown("---")
        st.markdown("#### మీ ప్రొఫైల్ వివరాలు")
        st.write(f"**నా గురించి:** {current_user_data.get('about', 'ఇంకా వివరాలు లేవు.')}")
        st.write(f"**పుట్టిన తేదీ:** {current_user_data.get('dob', 'ఇంకా వివరాలు లేవు.')}")


        st.markdown("---")
        st.markdown("#### మీ ఇటీవలి పోస్ట్‌లు")
        if not POSTS_CSV.exists() 
