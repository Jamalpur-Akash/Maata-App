import streamlit as st
import pandas as pd
import os
import time
import uuid
from pathlib import Path
from PIL import Image, UnidentifiedImageError
from datetime import datetime
import pytz
from deep_translator import GoogleTranslator

st.set_page_config(
    page_title="మాట - కమ్యూనిటీ",
    page_icon="👋",
    layout="centered",
    initial_sidebar_state="auto"
)

STORAGE_DIR = Path("storage/uploads")
PROFILE_DIR = Path("storage/profiles")
POSTS_CSV = Path("storage/posts.csv")
PROFILE_CSV = Path("storage/user_profiles.csv")

STORAGE_DIR.mkdir(parents=True, exist_ok=True)
PROFILE_DIR.mkdir(parents=True, exist_ok=True)
POSTS_CSV.touch(exist_ok=True)
PROFILE_CSV.touch(exist_ok=True)

if 'username' not in st.session_state:
    st.session_state.username = 'hello'
if 'language' not in st.session_state:
    st.session_state.language = 'Telugu'

def translate_text(text, target_lang):
    if not text or target_lang == 'English':
        return text
    try:
        return GoogleTranslator(source='auto', target=target_lang.lower()).translate(text)
    except:
        return text

lang_map = {
    "English": "English",
    "తెలుగు": "Telugu",
    "हिंदी": "Hindi"
}

language = st.selectbox("🌐 Language / భాష / भाषा", list(lang_map.keys()))
st.session_state.language = language
lang = lang_map[language]

def get_translated(label_dict):
    return label_dict.get(lang, label_dict["English"])

st.markdown(f"### 📢 {get_translated({'English': 'Posts', 'Telugu': 'పోస్ట్‌లు', 'Hindi': 'पोस्ट्स'})}")

if POSTS_CSV.stat().st_size != 0:
    df = pd.read_csv(POSTS_CSV)
    df = df.sort_values(by="timestamp", ascending=False)
    for i, row in df.iterrows():
        username = f"**@{row['username']}**"
        tz = pytz.timezone("Asia/Kolkata")
        timestamp = datetime.fromisoformat(row['timestamp']).astimezone(tz).strftime('%Y-%m-%d %H:%M:%S %Z')
        st.markdown(f"{username} {timestamp}")

        translated_text = translate_text(row['text'], lang)
        st.markdown(f"{translated_text}")

        if pd.notna(row['image']):
            image_path = Path(row['image'])
            if image_path.exists():
                try:
                    image = Image.open(image_path)
                    st.image(image, use_container_width=True)
                except UnidentifiedImageError:
                    st.warning(get_translated({
                        "English": "Unable to display image.",
                        "Telugu": "చిత్రాన్ని ప్రదర్శించలేరు.",
                        "Hindi": "छवि प्रदर्शित नहीं हो सकी।"
                    }))

        delete_label = get_translated({"English": "Delete", "Telugu": "తొలగించు", "Hindi": "हटाएं"})
        if st.button(delete_label, key=f"delete_{i}"):
            df = df.drop(i)
            df.to_csv(POSTS_CSV, index=False)
            st.experimental_rerun()

st.markdown("---")
st.markdown(get_translated({
    "English": "Create a new post",
    "Telugu": "కొత్త పోస్ట్ చేయండి",
    "Hindi": "नई पोस्ट बनाएँ"
}))

text_input = st.text_area(get_translated({
    "English": "What's on your mind?",
    "Telugu": "మీ మనసులో ఏముంది?",
    "Hindi": "आपके मन में क्या है?"
}), key="post_text")

image_file = st.file_uploader(get_translated({
    "English": "Upload Image (optional)",
    "Telugu": "చిత్రాన్ని అప్‌లోడ్ చేయండి (ఐచ్ఛికం)",
    "Hindi": "छवि अपलोड करें (वैकल्पिक)"
}), type=["png", "jpg", "jpeg"])

if st.button(get_translated({
    "English": "Post",
    "Telugu": "పోస్ట్ చేయండి",
    "Hindi": "पोस्ट करें"
})):
    new_id = str(uuid.uuid4())
    image_path = ""
    if image_file is not None:
        image_path = str(STORAGE_DIR / f"{new_id}_{image_file.name}")
        with open(image_path, "wb") as f:
            f.write(image_file.read())
    timestamp = datetime.now(pytz.utc).isoformat()
    new_post = {
        "id": new_id,
        "username": st.session_state.username,
        "text": text_input,
        "image": image_path,
        "timestamp": timestamp
    }
    df = pd.read_csv(POSTS_CSV) if POSTS_CSV.stat().st_size != 0 else pd.DataFrame(columns=new_post.keys())
    df = pd.concat([df, pd.DataFrame([new_post])], ignore_index=True)
    df.to_csv(POSTS_CSV, index=False)
    st.experimental_rerun()
