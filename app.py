import streamlit as st
import pandas as pd
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from deep_translator import GoogleTranslator
import pytz

st.set_page_config(page_title="Maata Project", layout="centered")
STORAGE_DIR = Path("storage/uploads")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

if "username" not in st.session_state:
    st.session_state.username = "Nanda kishor Reddy"

if "language" not in st.session_state:
    st.session_state.language = "Telugu"

lang_map = {
    "Telugu": "te",
    "Hindi": "hi",
    "English": "en"
}

def translate_text(text, lang_code):
    try:
        return GoogleTranslator(source='auto', target=lang_code).translate(text)
    except Exception:
        return text

POSTS_FILE = "posts.csv"

def load_posts():
    if os.path.exists(POSTS_FILE):
        return pd.read_csv(POSTS_FILE)
    else:
        return pd.DataFrame(columns=["id", "username", "text", "image_path", "timestamp"])

def save_post(username, text, image_path):
    df = load_posts()
    post_id = str(uuid.uuid4())
    timestamp = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")
    new_post = {"id": post_id, "username": username, "text": text, "image_path": image_path, "timestamp": timestamp}
    df = pd.concat([pd.DataFrame([new_post]), df], ignore_index=True)
    df.to_csv(POSTS_FILE, index=False)

LIKES_FILE = "likes.csv"
COMMENTS_FILE = "comments.csv"

def load_likes():
    if os.path.exists(LIKES_FILE):
        return pd.read_csv(LIKES_FILE)
    else:
        return pd.DataFrame(columns=["post_id", "username"])

def save_like(post_id, username):
    df = load_likes()
    if not ((df.post_id == post_id) & (df.username == username)).any():
        df = pd.concat([df, pd.DataFrame([{"post_id": post_id, "username": username}])], ignore_index=True)
        df.to_csv(LIKES_FILE, index=False)

def count_likes(post_id):
    df = load_likes()
    return len(df[df.post_id == post_id])

def load_comments():
    if os.path.exists(COMMENTS_FILE):
        return pd.read_csv(COMMENTS_FILE)
    else:
        return pd.DataFrame(columns=["post_id", "username", "comment", "timestamp"])

def save_comment(post_id, username, comment):
    df = load_comments()
    timestamp = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")
    new_comment = {"post_id": post_id, "username": username, "comment": comment, "timestamp": timestamp}
    df = pd.concat([df, pd.DataFrame([new_comment])], ignore_index=True)
    df.to_csv(COMMENTS_FILE, index=False)

def get_comments(post_id):
    df = load_comments()
    return df[df.post_id == post_id]

st.sidebar.markdown(f"### Hello, {st.session_state.username}")
page = st.sidebar.radio("Navigation", ["Home", "New Post", "Profile", "Logout"])

lang_option = st.selectbox("🌐 Language / भाषा / భాష", ["Telugu", "Hindi", "English"])
st.session_state.language = lang_option
lang_code = lang_map[st.session_state.language]

if page == "Home":
    st.markdown(f"### 📢 {translate_text('Posts', lang_code)}")

    df = load_posts()
    for _, row in df.iterrows():
        st.markdown(f"**@{row['username']}** ⏰ {row['timestamp']}")
        st.write(translate_text(row['text'], lang_code))
        if row["image_path"] and os.path.exists(row["image_path"]):
            st.image(row["image_path"], use_container_width=True)

        if st.button(f"👍 {translate_text('Like', lang_code)}", key=f"like_{row['id']}"):
            save_like(row['id'], st.session_state.username)
            st.experimental_rerun()
        st.caption(f"{count_likes(row['id'])} 👍")

        comment = st.text_input(f"{translate_text('Add a comment', lang_code)}:", key=f"comment_input_{row['id']}")
        if st.button(translate_text("Post Comment", lang_code), key=f"comment_btn_{row['id']}"):
            save_comment(row['id'], st.session_state.username, comment)
            st.experimental_rerun()

        for _, comment_row in get_comments(row['id']).iterrows():
            st.markdown(f"💬 **{comment_row['username']}**: {comment_row['comment']}")

        st.markdown("🔗 " + translate_text("Share link: ", lang_code) + f"https://yourapp.com/post/{row['id']}")
        st.markdown("---")

elif page == "New Post":
    st.markdown(f"### ✍️ {translate_text('Create a Post', lang_code)}")
    text = st.text_area(translate_text("What's on your mind?", lang_code))

    image = st.file_uploader(translate_text("Upload an image", lang_code), type=["jpg", "jpeg", "png"])

    if st.button(translate_text("Post", lang_code)):
        image_path = ""
        if image:
            image_path = str(STORAGE_DIR / f"{uuid.uuid4()}.png")
            with open(image_path, "wb") as f:
                f.write(image.read())
        save_post(st.session_state.username, text, image_path)
        st.success(translate_text("Posted successfully!", lang_code))
        st.experimental_rerun()

elif page == "Profile":
    st.markdown(f"### 🙍‍♂️ {translate_text('Your Profile', lang_code)}")
    st.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=100)
    st.write("**Username:**", st.session_state.username)
    st.write("**Email:** example@example.com")
    st.write("**About:** Passionate user of Maata Project.")
    st.write("**DOB:** 01-01-2000")

elif page == "Logout":
    st.session_state.username = ""
    st.success(translate_text("Logged out successfully.", lang_code))
