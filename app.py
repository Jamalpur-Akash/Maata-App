
# Our brand new app
import streamlit as st
import pandas as pd
import os
import time
import uuid # For unique filenames, especially for media uploads
from pathlib import Path # For cleaner path handling

# --- Configuration & Initial Setup ---

# Set page config for a professional look
st.set_page_config(
    page_title="మాట - కమ్యూనిటీ", # "Maata - Community"
    page_icon="👋",
    layout="centered", # Can be "wide" for more space
    initial_sidebar_state="auto"
)

# Define Storage Directories and CSV Files
STORAGE_DIR = Path("storage/uploads")
USER_CSV = STORAGE_DIR / "users.csv"
POSTS_CSV = STORAGE_DIR / "posts.csv"

# Ensure directories exist
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Initialize users.csv
if not USER_CSV.exists():
    pd.DataFrame(columns=["username", "password", "email"]).to_csv(USER_CSV, index=False)

# Initialize posts.csv
if not POSTS_CSV.exists():
    pd.DataFrame(columns=["post_id", "username", "timestamp", "caption", "media_path"]).to_csv(POSTS_CSV, index=False)

# --- Helper Functions ---

# Function to save posts
def save_post(username, caption, media_file=None):
    """Saves post details to CSV and media file to storage."""
    post_id = str(uuid.uuid4()) # Generate a unique ID for the post
    media_path = ""
    if media_file:
        # Create a unique filename for the uploaded media
        file_extension = Path(media_file.name).suffix
        media_filename = f"{post_id}{file_extension}"
        media_path = str(STORAGE_DIR / media_filename)

        # Save the media file
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
    return True # Indicate success

# Function to display posts
def display_posts():
    st.subheader("📢 కమ్యూనిటీ పోస్ట్‌లు") # "Community Posts"
    if not POSTS_CSV.exists() or POSTS_CSV.stat().st_size == 0:
        st.info("ఇంకా పోస్ట్‌లు లేవు! మొదట మీరే పంచుకోండి.") # "No posts yet! Be the first to share something."
        return

    posts_df = pd.read_csv(POSTS_CSV).sort_values(by="timestamp", ascending=False)

    if posts_df.empty:
        st.info("ఇంకా పోస్ట్‌లు లేవు! మొదట మీరే పంచుకోండి.") # "No posts yet! Be the first to share something."
        return

    for index, post in posts_df.iterrows():
        st.markdown(f"**@{post['username']}** <small>_{post['timestamp']}_</small>")
        st.write(post['caption'])
        if post['media_path'] and os.path.exists(post['media_path']):
            file_extension = Path(post['media_path']).suffix.lower()
            if file_extension in [".png", ".jpg", ".jpeg", ".gif"]:
                st.image(post['media_path'], use_column_width="always", caption=f"@{post['username']} ద్వారా పోస్ట్ చేయబడింది") # "Posted by @{username}"
            elif file_extension in [".mp4", ".mov", ".avi", ".webm"]:
                st.video(post['media_path'])
            else:
                st.warning(f"ఈ మీడియా రకం మద్దతు లేదు {post['media_path']}. ఫైల్ మార్గం చూపుతోంది.") # "Unsupported media type for {media_path}. Showing file path."
                st.write(post['media_path'])
        st.markdown("---") # Separator between posts

# --- Custom CSS for a professional touch ---
st.markdown(
    """
    <style>
    /* Ensure Telugu font support */
    body {
        font-family: 'NATS', 'Telugu', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol";
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: "Baloo Tammudu 2", 'Telugu', sans-serif; /* A bit more playful for headers */
        color: #2e7d32; /* A nice green accent */
    }
    .stButton>button {
        background-color: #4CAF50; /* Green */
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
    /* Style for the sidebar radio buttons */
    .stRadio > label {
        font-size: 1.1em;
        font-weight: bold;
        color: #1a5e20; /* Darker green for navigation */
    }
    .st-emotion-cache-16txt4v p, .st-emotion-cache-16txt4v div, .st-emotion-cache-16txt4v span { /* Target general text including in Telugu */
        font-size: 1.05em;
        line-height: 1.6;
    }
    /* Remove default Streamlit footer */
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

def login_signup():
    st.subheader("🔑 లాగిన్ / సైన్ అప్") # "Login / Sign Up"

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### ప్రస్తుత వినియోగదారు లాగిన్") # "Existing User Login"
        login_username = st.text_input("వినియోగదారు పేరు (లాగిన్)", key="login_username") # "Username (Login)"
        login_password = st.text_input("పాస్‌వర్డ్ (లాగిన్)", type="password", key="login_password") # "Password (Login)"
        if st.button("లాగిన్"): # "Login"
            users_df = pd.read_csv(USER_CSV)
            user_found = users_df[(users_df['username'] == login_username) & (users_df['password'] == login_password)]
            if not user_found.empty:
                st.session_state.logged_in = True
                st.session_state.username = login_username
                st.success(f"స్వాగతం, {login_username}!") # "Welcome back, {username}!"
                st.experimental_rerun() # Rerun to update UI
            else:
                st.error("తప్పు వినియోగదారు పేరు లేదా పాస్‌వర్డ్.") # "Invalid username or password."

    with col2:
        st.markdown("#### కొత్త వినియోగదారు సైన్ అప్") # "New User Sign Up"
        signup_username = st.text_input("వినియోగదారు పేరు (సైన్ అప్)", key="signup_username") # "Username (Sign Up)"
        signup_password = st.text_input("పాస్‌వర్డ్ (సైన్ అప్)", type="password", key="signup_password") # "Password (Sign Up)"
        signup_confirm_password = st.text_input("పాస్‌వర్డ్ నిర్ధారించండి", type="password", key="signup_confirm_password") # "Confirm Password"
        if st.button("సైన్ అప్"): # "Sign Up"
            if not signup_username or not signup_password or not signup_confirm_password:
                st.warning("దయచేసి అన్ని సైన్-అప్ ఫీల్డ్‌లను పూరించండి.") # "Please fill in all sign-up fields."
            elif signup_password != signup_confirm_password:
                st.error("పాస్‌వర్డ్‌లు సరిపోలడం లేదు.") # "Passwords do not match."
            else:
                users_df = pd.read_csv(USER_CSV)
                if signup_username in users_df['username'].values:
                    st.error("వినియోగదారు పేరు ఇప్పటికే ఉంది. దయచేసి మరొకటి ఎంచుకోండి.") # "Username already exists. Please choose another."
                else:
                    new_user = pd.DataFrame([{"username": signup_username, "password": signup_password, "email": ""}])
                    new_user.to_csv(USER_CSV, mode='a', header=False, index=False)
                    st.success("ఖాతా విజయవంతంగా సృష్టించబడింది! మీరు ఇప్పుడు లాగిన్ చేయవచ్చు.") # "Account created successfully! You can now login."

# --- Main App Logic ---
if not st.session_state.logged_in:
    login_signup()
else:
    st.sidebar.title(f"స్వాగతం, {st.session_state.username}!") # "Welcome, {username}!"
    st.sidebar.radio(
        "నావిగేషన్", # "Navigation"
        ("🏠 హోమ్", "📝 పోస్ట్", "👤 ప్రొఫైల్"), # "Home", "Post", "Profile"
        key="navigation_radio",
        help="పేజీని నావిగేట్ చేయడానికి ఎంచుకోండి." # "Select a page to navigate."
    )

    page = st.session_state.navigation_radio

    # --- Routing pages ---
    if page == "🏠 హోమ్": # "Home"
        st.subheader("💬 కమ్యూనిటీ పోస్ట్‌లు") # "Community Posts"
        display_posts()

    elif page == "📝 పోస్ట్": # "Post"
        st.subheader("✏️ కొత్త పోస్ట్ సృష్టించండి") # "Create a New Post"

        with st.form(key="new_post", clear_on_submit=True):
            col_caption, col_media = st.columns([2, 1])

            with col_caption:
                caption = st.text_area(
                    "ఏం జరుగుతోంది?", # "What's happening?"
                    height=150,
                    max_chars=500,
                    help="మీ ఆలోచనలు, భావాలు లేదా వార్తలను పంచుకోండి (గరిష్టంగా 500 అక్షరాలు)." # "Share your thoughts, feelings, or news (max 500 characters)."
                )
                if caption:
                    char_count = len(caption)
                    if char_count > 450:
                        st.warning(f"అక్షరాలు: {char_count}/500 - పరిమితికి దగ్గరగా ఉంది!") # "Characters: {count}/500 - Nearing limit!"
                    else:
                        st.info(f"అక్షరాలు: {char_count}/500") # "Characters: {count}/500"

            with col_media:
                st.markdown("---")
                media_file = st.file_uploader(
                    "చిత్రం/వీడియోను అప్‌లోడ్ చేయండి", # "Upload Image/Video"
                    type=["png", "jpg", "jpeg", "gif", "mp4", "mov", "avi", "webm"],
                    help="మద్దతు ఉన్న ఫార్మాట్‌లు: PNG, JPG, JPEG, GIF, MP4, MOV, AVI, WEBM. గరిష్టంగా 5MB సిఫార్సు చేయబడింది." # "Supported formats: ... Max 5MB recommended."
                )
                # Media Preview
                if media_file is not None:
                    file_size_mb = round(media_file.size / (1024 * 1024), 2)
                    st.success(f"ఫైల్ ఎంచుకోబడింది: {media_file.name} ({file_size_mb} MB)") # "File selected: {name} ({size} MB)"
                    if "image" in media_file.type:
                        st.image(media_file, caption="చిత్ర ప్రివ్యూ", width=150) # "Image Preview"
                    elif "video" in media_file.type:
                        st.video(media_file)
                    else:
                        st.info("ఫైల్ అప్‌లోడ్ చేయబడింది, కానీ ఈ రకానికి ప్రివ్యూ అందుబాటులో లేదు.") # "File uploaded, but no preview available for this type."


            submitted = st.form_submit_button("పోస్ట్ చేయండి") # "Share Post"

            if submitted:
                # --- Improved Validation ---
                if not caption.strip() and not media_file:
                    st.error("🚫 దయచేసి శీర్షికను జోడించండి లేదా భాగస్వామ్యం చేయడానికి చిత్రం/వీడియోను అప్‌లోడ్ చేయండి.") # "Please add a caption or upload an image/video to share."
                elif not caption.strip():
                    st.error("🚫 మీ పోస్ట్‌కు శీర్షిక అవసరం.") # "A caption is required for your post."
                elif media_file and media_file.size > 5 * 1024 * 1024:
                    st.error("🚫 మీడియా ఫైల్ చాలా పెద్దది. దయచేసి 5MB కంటే తక్కువ ఫైల్‌లను అప్‌లోడ్ చేయండి.") # "Media file too large. Please upload files smaller than 5MB."
                else:
                    # --- Progress and Loading Indicator ---
                    with st.spinner("🚀 మీ కంటెంట్‌ను పోస్ట్ చేస్తోంది... దయచేసి వేచి ఉండండి."): # "Posting your content... Please wait."
                        time.sleep(1) # Simulate network call/processing time
                        success = save_post(st.session_state.username, caption, media_file)

                    if success:
                        st.success("✅ మీ పోస్ట్ విజయవంతంగా భాగస్వామ్యం చేయబడింది!") # "Your post has been successfully shared!"
                        st.balloons()
                        # Optionally, switch to home page after successful post
                        # st.session_state.navigation_radio = "🏠 హోమ్"
                        # st.experimental_rerun()
                    else:
                        st.error("మీ పోస్ట్‌ను సేవ్ చేయడంలో ఏదో తప్పు జరిగింది. దయచేసి మళ్లీ ప్రయత్నించండి.") # "Something went wrong while saving your post. Please try again."

    elif page == "👤 ప్రొఫైల్": # "Profile"
        st.subheader(f"👤 {st.session_state.username} యొక్క ప్రొఫైల్") # "{username}'s Profile"
        st.write(f"**వినియోగదారు పేరు:** {st.session_state.username}") # "**Username:** {username}"

        st.markdown("---")
        st.markdown("#### మీ ఇటీవలి పోస్ట్‌లు") # "Your Recent Posts"
        if not POSTS_CSV.exists() or POSTS_CSV.stat().st_size == 0:
            st.info("మీరు ఇంకా ఏ పోస్ట్‌లు చేయలేదు.") # "You haven't made any posts yet."
        else:
            posts_df = pd.read_csv(POSTS_CSV)
            user_posts = posts_df[posts_df['username'] == st.session_state.username].sort_values(by="timestamp", ascending=False)
            if user_posts.empty:
                st.info("మీరు ఇంకా ఏ పోస్ట్‌లు చేయలేదు.") # "You haven't made any posts yet."
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
    if st.sidebar.button("లాగ్ అవుట్", help="మీ ఖాతా నుండి లాగ్ అవుట్ చేయడానికి క్లిక్ చేయండి."): # "Logout", "Click to log out of your account."
        st.session_state.logged_in = False
        st.session_state.username = None
        st.info("మీరు లాగ్ అవుట్ అయ్యారు.") # "You have been logged out."
        st.experimental_rerun()
          
    
        
        
        


