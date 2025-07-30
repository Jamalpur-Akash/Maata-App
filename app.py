import streamlit as st
import pandas as pd
import os
import time
import uuid
from datetime import datetime
import pytz
from pathlib import Path

st.set_page_config(page_title="మాట - కమ్యూనిటీ", page_icon="👋", layout="centered")

STORAGE_DIR = Path("storage/uploads")
USERS_FILE = Path("storage/users.csv")
POSTS_FILE = Path("storage/posts.csv")

STORAGE_DIR.mkdir(parents=True, exist_ok=True)
for file in [USERS_FILE, POSTS_FILE]:
    if not file.exists():
        file.write_text("username,email,password,about,dob,profile_pic\n" if "users" in file.name else "username,text,image_path,timestamp\n")

LANGUAGES = {"తెలుగు": "te", "हिंदी": "hi", "English": "en"}
if "lang" not in st.session_state:
    st.session_state.lang = "తెలుగు"

def t(te, hi, en):
    return {"తెలుగు": te, "हिंदी": hi, "English": en}[st.session_state.lang]

st.markdown("### 🔤 " + t("భాషను మార్చండి", "भाषा बदलें", "Switch Language"))
st.selectbox("", list(LANGUAGES.keys()), index=list(LANGUAGES.keys()).index(st.session_state.lang), key="lang")

def load_users():
    return pd.read_csv(USERS_FILE)

def load_posts():
    return pd.read_csv(POSTS_FILE)

def save_user(userdata):
    df = load_users()
    if userdata['username'] in df['username'].values:
        return False
    df = pd.concat([df, pd.DataFrame([userdata])], ignore_index=True)
    df.to_csv(USERS_FILE, index=False)
    return True

def save_post(username, text, image_path):
    df = load_posts()
    ist_time = datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S %Z")
    df = pd.concat([df, pd.DataFrame([{
        "username": username,
        "text": text,
        "image_path": image_path if image_path else "",
        "timestamp": ist_time
    }])], ignore_index=True)
    df.to_csv(POSTS_FILE, index=False)

def delete_post(index):
    df = load_posts()
    df = df.drop(index).reset_index(drop=True)
    df.to_csv(POSTS_FILE, index=False)

if "user" not in st.session_state:
    st.session_state.user = None

menu = st.sidebar.radio(t("నావిగేషన్", "नेविगेशन", "Navigation"),
    (t("హోమ్", "होम", "Home"),
     t("కొత్త పోస్ట్", "नई पोस्ट", "New Post"),
     t("ప్రొఫైల్", "प्रोफ़ाइल", "Profile"),
     t("లాగ్ అవుట్", "लॉग आउट", "Logout")))

if st.session_state.user:
    st.sidebar.markdown(f"👋 **{st.session_state.user}**")

if not st.session_state.user:
    st.title(t("మాట - తెలుగు కమ్యూనిటీ", "माटा - तेलुगु कम्युनिटी", "Maata - Telugu Community"))

    tab1, tab2 = st.tabs([t("లాగిన్", "लॉग इन", "Login"), t("నమోదు", "रजिस्टर", "Register")])

    with tab1:
        uname = st.text_input(t("వినియోగదారు పేరు", "उपयोगकर्ता नाम", "Username"))
        pwd = st.text_input(t("పాస్వర్డ్", "पासवर्ड", "Password"), type="password")
        if st.button(t("ప్రవేశించండి", "लॉग इन करें", "Login")):
            df = load_users()
            if uname in df['username'].values and df[df['username']==uname]['password'].iloc[0] == pwd:
                st.session_state.user = uname
                st.experimental_rerun()
            else:
                st.error(t("తప్పు సమాచారం", "गलत जानकारी", "Incorrect credentials"))

    with tab2:
        uname = st.text_input(t("వినియోగదారు పేరు", "उपयोगकर्ता नाम", "Username"), key="r_user")
        email = st.text_input("Email")
        pwd = st.text_input(t("పాస్వర్డ్", "पासवर्ड", "Password"), type="password", key="r_pass")
        if st.button(t("నమోదు", "रजिस्टर", "Register")):
            df = load_users()
            if uname in df['username'].values:
                st.warning(t("మీరు ఇప్పటికే నమోదు చేసుకున్నారు", "आप पहले ही पंजीकृत हैं", "You are already registered"))
            else:
                save_user({"username": uname, "email": email, "password": pwd, "about": "", "dob": "", "profile_pic": ""})
                st.success(t("నమోదు పూర్తయింది", "पंजीकरण सफल", "Registration successful"))

elif menu == t("లాగ్ అవుట్", "लॉग आउट", "Logout"):
    st.session_state.user = None
    st.experimental_rerun()

elif menu == t("ప్రొఫైల్", "प्रोफ़ाइल", "Profile"):
    df = load_users()
    user_data = df[df['username'] == st.session_state.user].iloc[0]
    st.header(t("ప్రొఫైల్ సమాచారం", "प्रोफ़ाइल विवरण", "Profile Details"))
    st.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=100)
    about = st.text_area(t("మీ గురించి", "आपके बारे में", "About"), user_data['about'])
    dob = st.date_input(t("పుట్టిన తేదీ", "जन्म तिथि", "Date of Birth"), pd.to_datetime(user_data['dob']) if user_data['dob'] else None)
    if st.button(t("సేవ్ చేయండి", "सेव करें", "Save")):
        df.loc[df['username'] == st.session_state.user, 'about'] = about
        df.loc[df['username'] == st.session_state.user, 'dob'] = dob.strftime("%Y-%m-%d")
        df.to_csv(USERS_FILE, index=False)
        st.success(t("సేవ్ అయింది", "सेव किया गया", "Saved"))

elif menu == t("కొత్త పోస్ట్", "नई पोस्ट", "New Post"):
    st.header(t("పోస్ట్ సృష్టించండి", "पोस्ट बनाएं", "Create Post"))
    txt = st.text_area(t("పోస్ట్ టెక్స్ట్", "पोस्ट टेक्स्ट", "Post Text"))
    img = st.file_uploader(t("చిత్రాన్ని ఎంచుకోండి", "छवि चुनें", "Choose Image"), type=["png", "jpg", "jpeg"])
    if st.button(t("పోస్ట్ చేయండి", "पोस्ट करें", "Post")):
        image_path = ""
        if img:
            filename = f"{uuid.uuid4().hex}_{img.name}"
            image_path = str(STORAGE_DIR / filename)
            with open(image_path, "wb") as f:
                f.write(img.read())
        save_post(st.session_state.user, txt, image_path)
        st.success(t("పోస్ట్ విజయవంతం", "पोस्ट सफल", "Post successful"))

else:
    st.header("📢 " + t("పోస్టులు", "पोस्ट्स", "Posts"))
    posts = load_posts()
    for i, row in posts[::-1].iterrows():
        st.markdown(f"**@{row['username']}** ({row['timestamp']})")
        st.write(row['text'])
        if row['image_path']:
            st.image(row['image_path'], use_column_width=True)
        if row['username'] == st.session_state.user:
            if st.button(t("తొలగించండి", "हटाएं", "Delete"), key=f"del_{i}"):
                delete_post(i)
                st.experimental_rerun()
