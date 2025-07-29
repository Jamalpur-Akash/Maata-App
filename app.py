import streamlit as st
import pandas as pd
import os
import time
import uuid
from pathlib import Path

# --- Configuration & Initial Setup ---

st.set_page_config(
    page_title="మాట - కమ్యూనిటీ",
    page_icon="👋",
    layout="centered",
    initial_sidebar_state="auto"
)

STORAGE_DIR = Path("storage/uploads")
USER_CSV = STORAGE_DIR / "users.csv"
POSTS_CSV = STORAGE_DIR / "posts.csv"

STORAGE_DIR.mkdir(parents=True, exist_ok=True)

if not USER_CSV.exists():
    pd.DataFrame(columns=["username", "password", "email"]).to_csv(USER_CSV, index=False)

if not POSTS_CSV.exists():
    pd.DataFrame(columns=["post_id", "username", "timestamp", "caption", "media_path"]).to_csv(POSTS_CSV, index=False)

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

def display_posts():
    st.subheader("📢 కమ్యూనిటీ పోస్ట్‌లు")
    if not POSTS_CSV.exists() or POSTS_CSV.stat().st_size == 0:
        st.info("ఇంకా పోస్ట్‌లు లేవు! మొదట మీరే పంచుకోండి.")
        return

    posts_df = pd.read_csv(POSTS_CSV).sort_values(by="timestamp", ascending=False)

    if posts_df.empty:
        st.info("ఇంకా పోస్ట్‌లు లేవు! మొదట మీరే పంచుకోండి.")
        return

    for index, post in posts_df.iterrows():
        st.markdown(f"**@{post['username']}** <small>_{post['timestamp']}_</small>")
        st.write(post['caption'])
        if post['media_path'] and os.path.exists(post['media_path']):
            file_extension = Path(post['media_path']).suffix.lower()
            if file_extension in [".png", ".jpg", ".jpeg", ".gif"]:
                st.image(post['media_path'], use_column_width="always", caption=f"@{post['username']} ద్వారా పోస్ట్ చేయబడింది")
            elif file_extension in [".mp4", ".mov", ".avi", ".webm"]:
                st.video(post['media_path'])
            else:
                st.warning(f"ఈ మీడియా రకం మద్దతు లేదు {post['media_path']}. ఫైల్ మార్గం చూపుతోంది.")
                st.write(post['media_path'])
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
# Initialize session state variables at the top level
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'login_status_message' not in st.session_state:
    st.session_state.login_status_message = "" # To store temporary login messages

def login_signup():
    st.subheader("🔑 లాగిన్ / సైన్ అప్")

    # Display any previous login/signup status messages
    if st.session_state.login_status_message:
        if "విజయవంతంగా" in st.session_state.login_status_message or "స్వాగతం" in st.session_state.login_status_message:
            st.success(st.session_state.login_status_message)
        elif "తప్పు" in st.session_state.login_status_message or "సరిపోలడం లేదు" in st.session_state.login_status_message or "ఇప్పటికే ఉంది" in st.session_state.login_status_message:
            st.error(st.session_state.login_status_message)
        else:
            st.warning(st.session_state.login_status_message)
        st.session_state.login_status_message = "" # Clear message after displaying

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
                # No explicit rerun needed. The next full Streamlit rerun will show the main app.
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
                    new_user = pd.DataFrame([{"username": signup_username, "password": signup_password, "email": ""}])
                    new_user.to_csv(USER_CSV, mode='a', header=False, index=False)
                    st.session_state.login_status_message = "ఖాతా విజయవంతంగా సృష్టించబడింది! మీరు ఇప్పుడు లాగిన్ చేయవచ్చు."

# --- Main App Logic ---
# The core logic is now entirely driven by st.session_state.logged_in
if not st.session_state.logged_in:
    login_signup()
else:
    # If logged in, show the main app content
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
        st.write(f"**వినియోగదారు పేరు:** {st.session_state.username}")

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
                            st.image(post['media_path'], use_column_width="always")
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
        st.session_state.login_status_message = "మీరు లాగ్ అవుట్ అయ్యారు." # Set logout message
        # No explicit rerun here, rely on Streamlit's natural re-run due to state change
