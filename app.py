import streamlit as st
import pandas as pd
import os
import time
import uuid
from datetime import datetime
import pytz

st.set_page_config(page_title="మాట ప్రాజెక్ట్", layout="centered")

if 'language' not in st.session_state:
    st.session_state.language = 'te'

lang_options = {
    'te': 'తెలుగు',
    'hi': 'हिंदी',
    'en': 'English'
}

translations = {
    'post': {'te': 'పోస్ట్', 'hi': 'पोस्ट', 'en': 'Post'},
    'home': {'te': 'హోమ్', 'hi': 'होम', 'en': 'Home'},
    'new_post': {'te': 'కొత్త పోస్ట్', 'hi': 'नई पोस्ट', 'en': 'New Post'},
    'profile': {'te': 'ప్రొఫైల్', 'hi': 'प्रोफाइल', 'en': 'Profile'},
    'logout': {'te': 'లాగ్ అవుట్', 'hi': 'लॉग आउट', 'en': 'Logout'},
    'already_registered': {'te': 'మీరు ఇప్పటికే నమోదు చేసుకున్నారు', 'hi': 'आप पहले ही रजिस्टर कर चुके हैं', 'en': 'You are already registered'},
}

def t(key):
    return translations.get(key, {}).get(st.session_state.language, key)

st.selectbox("🌐", options=list(lang_options.keys()), format_func=lambda x: lang_options[x], key="language")

PERSIST_FILE = "posts.csv"
PROFILE_FILE = "profiles.csv"

def load_posts():
    if os.path.exists(PERSIST_FILE):
        return pd.read_csv(PERSIST_FILE)
    return pd.DataFrame(columns=["id", "username", "text", "image", "timestamp"])

def save_posts(posts):
    posts.to_csv(PERSIST_FILE, index=False)

def load_profiles():
    if os.path.exists(PROFILE_FILE):
        return pd.read_csv(PROFILE_FILE)
    return pd.DataFrame(columns=["username", "email", "about", "dob", "photo"])

def save_profiles(df):
    df.to_csv(PROFILE_FILE, index=False)

def display_post(row):
    st.markdown(f"**@{row['username']}** ({row['timestamp']})")
    st.write(row['text'])
    if row['image'] and os.path.exists(row['image']):
        st.image(row['image'], use_container_width=True)

    if st.session_state.username == row['username']:
        if st.button("🗑️ Delete", key=f"del_{row['id']}"):
            posts_df.drop(posts_df[posts_df['id'] == row['id']].index, inplace=True)
            save_posts(posts_df)
            st.experimental_rerun()

def profile_ui():
    st.subheader(t('profile'))
    profiles = load_profiles()
    profile = profiles[profiles['username'] == st.session_state.username]

    if not profile.empty:
        data = profile.iloc[0]
        st.image("default_profile_icon.png", width=80)
        st.write(f"**Email:** {data['email']}")
        st.write(f"**About:** {data['about']}")
        st.write(f"**DOB:** {data['dob']}")
    else:
        st.warning("Profile not found.")

def signup_ui():
    st.title("సైన్ అప్")
    username = st.text_input("Username")
    email = st.text_input("Email")
    about = st.text_area("About")
    dob = st.date_input("Date of Birth")
    if st.button("Register"):
        profiles = load_profiles()
        if username in profiles["username"].values:
            st.error(t("already_registered"))
        else:
            new = pd.DataFrame([{"username": username, "email": email, "about": about, "dob": dob, "photo": "default_profile_icon.png"}])
            save_profiles(pd.concat([profiles, new], ignore_index=True))
            st.success("Registered! Please reload to login.")

def new_post_ui():
    st.subheader(t('new_post'))
    text = st.text_area("Say something...")
    image = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"])
    img_path = None
    if image:
        img_path = os.path.join("storage", f"{uuid.uuid4()}.png")
        with open(img_path, "wb") as f:
            f.write(image.getbuffer())
    if st.button("Post"):
        now = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")
        new = pd.DataFrame([{"id": str(uuid.uuid4()), "username": st.session_state.username, "text": text, "image": img_path, "timestamp": now}])
        save_posts(pd.concat([posts_df, new], ignore_index=True))
        st.success("Posted!")
        st.experimental_rerun()

def home_ui():
    st.subheader(t("post"))
    for _, row in posts_df[::-1].iterrows():
        display_post(row)

def sidebar():
    st.sidebar.title("నావిగేషన్")
    page = st.sidebar.radio("", [t("home"), t("new_post"), t("profile"), t("logout")])
    return page

def login_ui():
    st.title("లాగిన్")
    username = st.text_input("Username")
    if st.button("Login"):
        st.session_state.username = username
        st.experimental_rerun()

if 'username' not in st.session_state:
    login_ui()
else:
    posts_df = load_posts()
    st.sidebar.markdown(f"👋 హలో, {st.session_state.username}")
    page = sidebar()

    if page == t("home"):
        home_ui()
    elif page == t("new_post"):
        new_post_ui()
    elif page == t("profile"):
        profile_ui()
    elif page == t("logout"):
        del st.session_state.username
        st.experimental_rerun()
