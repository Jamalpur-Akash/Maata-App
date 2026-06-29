import streamlit as st
import pandas as pd
import os
import time
import uuid
from pathlib import Path
from persistence import load_all_from_hub, save_file_to_hub

if 'hub_loaded' not in st.session_state:
    load_all_from_hub()
    st.session_state.hub_loaded = True

st.set_page_config(page_title="మాట - కమ్యూనిటీ", page_icon="📰", layout="centered")

STORAGE_DIR = Path("storage/uploads")
USER_CSV = STORAGE_DIR / "users.csv"
POSTS_CSV = STORAGE_DIR / "posts.csv"
INTERACTIONS_CSV = STORAGE_DIR / "interactions.csv"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

if not USER_CSV.exists():
    pd.DataFrame(columns=["username", "password", "email", "about", "dob"]).to_csv(USER_CSV, index=False)
else:
    df = pd.read_csv(USER_CSV)
    if 'about' not in df.columns:
        df['about'] = ''
    if 'dob' not in df.columns:
        df['dob'] = ''
    if 'email' not in df.columns:
        df['email'] = ''
    df.to_csv(USER_CSV, index=False)

if not POSTS_CSV.exists():
    pd.DataFrame(columns=["post_id", "username", "timestamp", "caption", "media_path"]).to_csv(POSTS_CSV, index=False)

if not INTERACTIONS_CSV.exists():
    pd.DataFrame(columns=["interaction_id", "post_id", "username", "type", "content", "timestamp"]).to_csv(INTERACTIONS_CSV, index=False)

def save_post(username, caption, media_file=None):
    post_id = str(uuid.uuid4())
    media_path = ""
    if media_file:
        ext = Path(media_file.name).suffix
        media_filename = f"{post_id}{ext}"
        media_path = str(STORAGE_DIR / media_filename)
        with open(media_path, "wb") as f:
            f.write(media_file.getbuffer())
    timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    pd.DataFrame([{
        "post_id": post_id,
        "username": username,
        "timestamp": timestamp,
        "caption": caption,
        "media_path": media_path
    }]).to_csv(POSTS_CSV, mode='a', header=False, index=False)

    save_file_to_hub(str(POSTS_CSV))
        if media_path:
            save_file_to_hub(media_path)

def delete_post(post_id):
    posts_df = pd.read_csv(POSTS_CSV)
    posts_df = posts_df[posts_df["post_id"] != post_id]
    posts_df.to_csv(POSTS_CSV, index=False)
    interactions_df = pd.read_csv(INTERACTIONS_CSV)
    interactions_df = interactions_df[interactions_df["post_id"] != post_id]
    interactions_df.to_csv(INTERACTIONS_CSV, index=False)

def record_interaction(post_id, username, interaction_type, content=""):
    interaction_id = str(uuid.uuid4())
    timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    pd.DataFrame([{
        "interaction_id": interaction_id,
        "post_id": post_id,
        "username": username,
        "type": interaction_type,
        "content": content,
        "timestamp": timestamp
    }]).to_csv(INTERACTIONS_CSV, mode='a', header=False, index=False)

def remove_interaction(interaction_id):
    df = pd.read_csv(INTERACTIONS_CSV)
    df = df[df['interaction_id'] != interaction_id]
    df.to_csv(INTERACTIONS_CSV, index=False)

def get_post_interactions(post_id):
    if not INTERACTIONS_CSV.exists() or INTERACTIONS_CSV.stat().st_size == 0:
        return {'likes_count': 0, 'comments_df': pd.DataFrame(), 'user_like_id': None}
    df = pd.read_csv(INTERACTIONS_CSV)
    df_post = df[df['post_id'] == post_id]
    likes = df_post[df_post['type'] == 'like']
    comments = df_post[df_post['type'] == 'comment'].sort_values(by="timestamp")
    user_like_id = None
    if st.session_state.get("logged_in"):
        user_like = likes[likes["username"] == st.session_state.username]
        if not user_like.empty:
            user_like_id = user_like.iloc[0]['interaction_id']
    return {'likes_count': likes.shape[0], 'comments_df': comments, 'user_like_id': user_like_id}

def display_posts():
    st.subheader("📢 పోస్ట్‌లు")
    if not POSTS_CSV.exists() or POSTS_CSV.stat().st_size == 0:
        st.info("ఇంకా పోస్ట్‌లు లేవు!")
        return
    df = pd.read_csv(POSTS_CSV).sort_values(by="timestamp", ascending=False)
    for _, row in df.iterrows():
        st.markdown(f"**@{row['username']}** _{row['timestamp']}_")
        st.write(row['caption'])
        if row['media_path'] and os.path.exists(row['media_path']):
            ext = Path(row['media_path']).suffix.lower()
            if ext in [".png", ".jpg", ".jpeg", ".gif"]:
                st.image(row['media_path'], use_container_width=True)
            elif ext in [".mp4", ".mov", ".avi", ".webm"]:
                st.video(row['media_path'])

        interactions = get_post_interactions(row['post_id'])
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        with col1:
            if interactions['user_like_id']:
                if st.button(f"❤️ ({interactions['likes_count']})", key=row['post_id'] + "_unlike"):
                    remove_interaction(interactions['user_like_id'])
                    st.rerun()
            else:
                if st.button(f"👍 ({interactions['likes_count']})", key=row['post_id'] + "_like"):
                    record_interaction(row['post_id'], st.session_state.username, "like")
                    st.rerun()
        with col2:
            st.write(f"💬 {interactions['comments_df'].shape[0]}")
        with col3:
            st.button("🔗", key=row['post_id'] + "_share", disabled=True)
        with col4:
            if row['username'] == st.session_state.username:
                if st.button("🗑️", key=row['post_id'] + "_delete"):
                    delete_post(row['post_id'])
                    st.rerun()

        with st.expander("వ్యాఖ్యలు"):
            for _, c in interactions['comments_df'].iterrows():
                st.markdown(f"**@{c['username']}** _{c['timestamp']}_")
                st.write(c['content'])
            comment = st.text_input("మీ వ్యాఖ్య...", key=row['post_id'] + "_input")
            if st.button("వ్యాఖ్య పంపండి", key=row['post_id'] + "_submit"):
                if comment.strip():
                    record_interaction(row['post_id'], st.session_state.username, "comment", comment)
                    st.rerun()
        st.markdown("---")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'auth_view' not in st.session_state:
    st.session_state.auth_view = "login"

def login_signup():
    st.title("మాట - తెలుగు కమ్యూనిటీ 🌸")
    st.markdown("మీ భావాలను పంచుకోండి, ఇతరులతో అనుభవం ఆవిష్కరించండి!")
    option = st.radio("మెను ఎంచుకోండి", ["లాగిన్", "సైన్ అప్"])
    if option == "లాగిన్":
        user = st.text_input("వినియోగదారు పేరు")
        pwd = st.text_input("పాస్‌వర్డ్", type="password")
        if st.button("లాగిన్"):
            df = pd.read_csv(USER_CSV)
            if not df[(df.username == user) & (df.password == pwd)].empty:
                st.session_state.logged_in = True
                st.session_state.username = user
                st.rerun()
            else:
                st.error("తప్పు వినియోగదారు పేరు లేదా పాస్‌వర్డ్.")
    else:
        user = st.text_input("వినియోగదారు పేరు (కొత్త)")
        email = st.text_input("ఈమెయిల్")
        pwd = st.text_input("పాస్‌వర్డ్", type="password")
        confirm = st.text_input("పాస్‌వర్డ్ నిర్ధారించండి", type="password")
        if st.button("సైన్ అప్"):
            df = pd.read_csv(USER_CSV)
            if user in df.username.values:
                st.error("మీరు ఇప్పటికే రిజిస్టర్ అయ్యారు.")
            elif pwd != confirm:
                st.error("పాస్‌వర్డ్‌లు సరిపోలలేదు.")
            else:
                new = pd.DataFrame([{"username": user, "password": pwd, "email": email, "about": "", "dob": ""}])
                new.to_csv(USER_CSV, mode="a", header=False, index=False)
                save_file_to_hub(str(USER_CSV))
                st.success("సైన్ అప్ విజయవంతం! లాగిన్ చేయండి.")
                st.session_state.auth_view = "login"
                st.rerun()

if not st.session_state.logged_in:
    login_signup()
else:
    st.sidebar.markdown(f"👋 హలో, {st.session_state.username}")
    nav = st.sidebar.radio("నావిగేషన్", ["🏠 హోమ్", "➕ కొత్త పోస్ట్", "👤 ప్రొఫైల్", "🔒 లాగ్ అవుట్"])
    if nav == "🏠 హోమ్":
        display_posts()
    elif nav == "➕ కొత్త పోస్ట్":
        st.subheader("మీ కొత్త పోస్ట్‌ను పంచుకోండి")
        with st.form("new_post", clear_on_submit=True):
            caption = st.text_area("ఏం జరుగుతోంది?")
            media = st.file_uploader("మీడియా జోడించండి", type=["png", "jpg", "jpeg", "gif", "mp4", "mov", "avi", "webm"])
            submit = st.form_submit_button("పోస్ట్ చేయండి")
            if submit:
                if not caption.strip() and not media:
                    st.error("కనీసం శీర్షిక లేదా మీడియా అవసరం.")
                else:
                    save_post(st.session_state.username, caption, media)
                    st.success("పోస్ట్ పంపబడింది!")
                    st.rerun()
    elif nav == "👤 ప్రొఫైల్":
        df = pd.read_csv(USER_CSV)
        user_data = df[df.username == st.session_state.username].iloc[0]
        st.markdown("### ప్రొఫైల్")
        st.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=100)
        st.write(f"**వినియోగదారు పేరు:** {st.session_state.username}")
        st.write(f"**ఈమెయిల్:** {user_data.email}")
        st.write(f"**నా గురించి:** {user_data.about}")
        st.write(f"**పుట్టిన తేదీ:** {user_data.dob}")
        with st.form("edit_profile"):
            new_about = st.text_area("నా గురించి", value=user_data.about)
            new_dob = st.text_input("పుట్టిన తేదీ (YYYY-MM-DD)", value=user_data.dob)
            submit = st.form_submit_button("సేవ్ చేయండి")
            if submit:
                df.loc[df.username == st.session_state.username, "about"] = new_about
                df.loc[df.username == st.session_state.username, "dob"] = new_dob
                df.to_csv(USER_CSV, index=False)
                st.success("నవీకరణ పూర్తైంది!")
                st.rerun()
    elif nav == "🔒 లాగ్ అవుట్":
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()
