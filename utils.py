import pandas as pd
import streamlit as st
from datetime import datetime
import os

POSTS_CSV = "storage/posts.csv"
UPLOAD_DIR = "storage/uploads/"

def load_posts():
    if os.path.exists(POSTS_CSV):
        return pd.read_csv(POSTS_CSV)
    return pd.DataFrame(columns=["timestamp", "username", "caption", "media_path"])

def save_post(username, caption, media_file):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    media_path = ""

    if media_file:
        file_ext = media_file.name.split('.')[-1]
        file_name = f"{username}_{int(datetime.now().timestamp())}.{file_ext}"
        media_path = os.path.join(UPLOAD_DIR, file_name)
        with open(media_path, "wb") as f:
            f.write(media_file.getbuffer())

    new_post = pd.DataFrame([[timestamp, username, caption, media_path]],
                            columns=["timestamp", "username", "caption", "media_path"])
    old_posts = load_posts()
    updated_posts = pd.concat([new_post, old_posts], ignore_index=True)
    updated_posts.to_csv(POSTS_CSV, index=False)

def display_posts():
    posts = load_posts()
    for _, row in posts.iterrows():
        st.markdown(f"**{row['username']}**  ·  _{row['timestamp']}_")
        st.write(row['caption'])

        if row['media_path']:
            if row['media_path'].endswith(('jpg', 'png', 'jpeg')):
                st.image(row['media_path'], use_column_width=True)
            elif row['media_path'].endswith('mp4'):
                st.video(row['media_path'])

        st.markdown("---")