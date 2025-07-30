import streamlit as st
from deep_translator import GoogleTranslator
import os
import uuid
from datetime import datetime
from pytz import timezone
from PIL import Image, UnidentifiedImageError
from pathlib import Path

st.set_page_config(page_title="మాట కమ్యూనిటీ", layout="centered")

if "language" not in st.session_state:
    st.session_state.language = "తెలుగు"

if "posts" not in st.session_state:
    st.session_state.posts = []

if "username" not in st.session_state:
    st.session_state.username = None

lang_map = {"తెలుగు": "te", "हिंदी": "hi", "English": "en"}
lang_choice = st.selectbox("🌐 Language / भाषा / భాష", options=["తెలుగు", "हिंदी", "English"])
st.session_state.language = lang_choice
lang_code = lang_map[lang_choice]

def t(text):
    return GoogleTranslator(source="auto", target=lang_code).translate(text)

def save_post(username, text, image_path):
    tz = timezone("Asia/Kolkata")
    time_now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z")
    post = {"username": username, "text": text, "image": image_path, "time": time_now}
    st.session_state.posts.insert(0, post)

def login_signup():
    st.radio(t("Login or Signup"), ["సైన్ ఇన్", "సైన్ అప్"], key="auth_mode", horizontal=True)
    username = st.text_input(t("Enter Username"))
    password = st.text_input(t("Password"), type="password")
    if st.button(t("Login")):
        if username and password:
            st.session_state.username = username
            st.experimental_rerun()

if not st.session_state.username:
    login_signup()
    st.stop()

st.sidebar.title("మాట ప్రాజెక్ట్")
nav = st.sidebar.radio("", [t("ప్రొఫైల్"), t("పోస్ట్ చేయి"), t("పోస్టులు")])

if nav == t("ప్రొఫైల్"):
    st.title(t("ప్రొఫైల్"))
    st.write(f"{t('Welcome')}, {st.session_state.username}")

elif nav == t("పోస్ట్ చేయి"):
    st.title(t("పోస్ట్ చేయి"))
    text = st.text_area(t("మీ సందేశాన్ని రాయండి"))
    img_file = st.file_uploader(t("ఛాయాచిత్రాన్ని అప్లోడ్ చేయండి"), type=["jpg", "png", "jpeg"])
    image_path = None
    if img_file:
        folder = Path("storage/uploads")
        folder.mkdir(parents=True, exist_ok=True)
        image_id = str(uuid.uuid4()) + ".jpg"
        image_path = folder / image_id
        with open(image_path, "wb") as f:
            f.write(img_file.read())
    if st.button(t("పోస్ట్")):
        if text:
            save_post(st.session_state.username, text, str(image_path) if image_path else "")
            st.success(t("పోస్ట్ విజయవంతం"))

elif nav == t("పోస్టులు"):
    st.title(f"📢 {t('Posts')}")
    for i, post in enumerate(st.session_state.posts):
        st.markdown(f"**@{post['username']}** _{post['time']}_")
        translated_text = GoogleTranslator(source="auto", target=lang_code).translate(post["text"])
        st.write(translated_text)
        if post["image"]:
            try:
                st.image(post["image"], use_container_width=True)
            except UnidentifiedImageError:
                st.warning(t("చిత్రాన్ని ప్రదర్శించలేకపోయాం"))
        if st.button(t("Delete"), key=f"delete_{i}"):
            st.session_state.posts.pop(i)
            st.experimental_rerun()
                            
