import streamlit as st
from datetime import datetime
import pytz
import uuid
import os
from pathlib import Path
from deep_translator import GoogleTranslator
from PIL import Image, UnidentifiedImageError
import io
import base64

st.set_page_config("మాట - కమ్యూనిటీ", "👋", "centered")

LANGUAGES = {"తెలుగు": "te", "हिन्दी": "hi", "English": "en"}
if "language" not in st.session_state:
    st.session_state.language = "తెలుగు"
if "posts" not in st.session_state:
    st.session_state.posts = []
if "username" not in st.session_state:
    st.session_state.username = "Nanda kishor Reddy"

def t(text):
    if st.session_state.language == "తెలుగు":
        return text
    return GoogleTranslator(source='auto', target=LANGUAGES[st.session_state.language]).translate(text)

def translate_post(post):
    lang = st.session_state.language
    if lang == "తెలుగు":
        return post
    translated_post = post.copy()
    for key in ["text", "timestamp", "username"]:
        if key in post and isinstance(post[key], str):
            translated_post[key] = GoogleTranslator(source='auto', target=LANGUAGES[lang]).translate(post[key])
    return translated_post

def save_post(text, image_file):
    post = {
        "id": str(uuid.uuid4()),
        "username": st.session_state.username,
        "text": text,
        "timestamp": datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S %Z"),
        "media_path": None
    }
    if image_file:
        media_path = f"storage/uploads/{uuid.uuid4()}.jpg"
        Path("storage/uploads").mkdir(parents=True, exist_ok=True)
        with open(media_path, "wb") as f:
            f.write(image_file.read())
        post["media_path"] = media_path
    st.session_state.posts.insert(0, post)

def post_section():
    st.subheader(t("పోస్ట్ చేయండి"))
    text = st.text_area(t("మీ సందేశం"), max_chars=500)
    image = st.file_uploader(t("ఛిత్రాన్ని అప్‌లోడ్ చేయండి"), type=["png", "jpg", "jpeg"])
    if st.button(t("ఈ పోస్ట్‌ను షేర్ చేయండి")):
        if text or image:
            save_post(text, image)
        else:
            st.warning(t("దయచేసి టెక్స్ట్ లేదా చిత్రం ఇవ్వండి"))

def display_posts():
    st.subheader(t("పోస్ట్‌లు"))
    for post in st.session_state.posts:
        post = translate_post(post)
        st.markdown(f"**@{post['username']}** • {post['timestamp']}")
        st.write(post["text"])
        if post.get("media_path"):
            try:
                with open(post["media_path"], "rb") as f:
                    image = Image.open(io.BytesIO(f.read()))
                    st.image(image, use_container_width=True)
            except UnidentifiedImageError:
                st.warning(t("చిత్రాన్ని లోడ్ చేయలేకపోయాం"))

st.sidebar.title(t("నావిగేషన్"))
option = st.sidebar.radio(t("మెనూ"), [t("🏠 హోమ్"), t("👤 ప్రొఫైల్"), t("📤 పోస్ట్ చేయండి")])
st.sidebar.selectbox("🌐 " + t("భాష"), list(LANGUAGES.keys()), index=list(LANGUAGES.keys()).index(st.session_state.language), key="language")

if option == t("🏠 హోమ్"):
    display_posts()
elif option == t("📤 పోస్ట్ చేయండి"):
    post_section()
    display_posts()
elif option == t("👤 ప్రొఫైల్"):
    st.subheader(t("నా హోమ్ పేజీ"))
    st.markdown(f"**{t('పేరు')}:** {st.session_state.username}")
    st.markdown(f"**{t('ఇమెయిల్')}:** user@example.com")
    st.markdown(f"**{t('జన్మతేదీ')}:** 2000-01-01")
    st.markdown(f"**{t('About')}:** {t('ప్రొఫైల్ వివరణ లభించలేదు')}")
        
