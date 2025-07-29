import streamlit as st
import pandas as pd
import os
import uuid
from pathlib import Path

# --- our page starting ---
st.set_page_config(page_title="మాట - తెలుగు కమ్యూనిటీ", page_icon="🌸", layout="centered")

STORAGE_DIR = Path("storage/uploads")
USER_CSV = STORAGE_DIR / "users.csv"
POSTS_CSV = STORAGE_DIR / "posts.csv"
INTERACTIONS_CSV = STORAGE_DIR / "interactions.csv"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Create CSVs if not exist
for file, cols in {
    USER_CSV: ["username", "password", "email", "about", "dob"],
    POSTS_CSV: ["post_id", "username", "timestamp", "caption", "media_path"],
    INTERACTIONS_CSV: ["interaction_id", "post_id", "username", "type", "content", "timestamp"]
}.items():
    if not file.exists():
        pd.DataFrame(columns=cols).to_csv(file, index=False)

# ---  CSS code---
st.markdown("""
    <style>
    body { background-color: #f9f9f9; }
    .stButton>button {
        border-radius: 8px;
        background-color: #6c5ce7;
        color: white;
        font-weight: bold;
    }
    .stTextInput>div>div>input,
    .stTextArea textarea {
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <h1 style='text-align: center; color: #6c5ce7;'>మాట - తెలుగు కమ్యూనిటీ 🌸</h1>
    <p style='text-align: center;'>మీ భావాలను పంచుకోండి, ఇతరులతో మమేకం అవ్వండి!</p>
    <hr style='border: 1px solid #ccc;'>
""", unsafe_allow_html=True)

# --- login and logout sessions ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None

# --- Interaction Helpers ---
def get_post_interactions(post_id):
    if not INTERACTIONS_CSV.exists():
        return {'likes_count': 0, 'comments_df': pd.DataFrame(), 'user_like_id': None}
    df = pd.read_csv(INTERACTIONS_CSV)
    df = df[df["post_id"] == post_id]
    likes = df[df["type"] == "like"]
    comments = df[df["type"] == "comment"]
    user_like = None
    if st.session_state.logged_in:
        user_likes = likes[likes["username"] == st.session_state.username]
        if not user_likes.empty:
            user_like = user_likes.iloc[0]["interaction_id"]
    return {'likes_count': len(likes), 'comments_df': comments, 'user_like_id': user_like}

def record_interaction(post_id, type_, content=""):
    df = pd.read_csv(INTERACTIONS_CSV)
    new_row = {
        "interaction_id": str(uuid.uuid4()),
        "post_id": post_id,
        "username": st.session_state.username,
        "type": type_,
        "content": content,
        "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    df.loc[len(df)] = new_row
    df.to_csv(INTERACTIONS_CSV, index=False)

# --- our posts section---
def display_posts():
    st.subheader("📢 పోస్టులు")
    if not POSTS_CSV.exists() or os.path.getsize(POSTS_CSV) == 0:
        st.info("ఇంకా పోస్ట్‌లు లేవు!")
        return

    posts_df = pd.read_csv(POSTS_CSV).sort_values("timestamp", ascending=False)
    for _, post in posts_df.iterrows():
        st.markdown("<div style='border:1px solid #dfe6e9; border-radius:10px; padding:15px; margin-bottom:20px;'>", unsafe_allow_html=True)
        st.markdown(f"**@{post['username']}** <span style='font-size:12px; color:#636e72;'>({post['timestamp']})</span>", unsafe_allow_html=True)
        st.write(post["caption"])
        if post["media_path"] and os.path.exists(post["media_path"]):
            ext = Path(post["media_path"]).suffix.lower()
            if ext in [".jpg", ".jpeg", ".png"]:
                st.image(post["media_path"])
            elif ext in [".mp4"]:
                st.video(post["media_path"])

        interactions = get_post_interactions(post["post_id"])
        col_like, col_comment_btn, col_delete = st.columns([1, 1, 1])

        with col_like:
            if interactions["user_like_id"]:
                if st.button("❤️ Unlike", key=f"unlike_{post['post_id']}"):
                    df = pd.read_csv(INTERACTIONS_CSV)
                    df = df[df["interaction_id"] != interactions["user_like_id"]]
                    df.to_csv(INTERACTIONS_CSV, index=False)
                    st.rerun()
            else:
                if st.button(f"👍 Like ({interactions['likes_count']})", key=f"like_{post['post_id']}"):
                    record_interaction(post["post_id"], "like")
                    st.rerun()

        with col_comment_btn:
            st.markdown(f"💬 {len(interactions['comments_df'])} వ్యాఖ్యలు")

        with col_delete:
            if post['username'] == st.session_state.username:
                if st.button("🗑️ తొలగించండి", key=f"delete_{post['post_id']}"):
                    posts_df = posts_df[posts_df['post_id'] != post['post_id']]
                    posts_df.to_csv(POSTS_CSV, index=False)
                    if INTERACTIONS_CSV.exists():
                        interactions_df = pd.read_csv(INTERACTIONS_CSV)
                        interactions_df = interactions_df[interactions_df['post_id'] != post['post_id']]
                        interactions_df.to_csv(INTERACTIONS_CSV, index=False)
                    if post['media_path'] and os.path.exists(post['media_path']):
                        os.remove(post['media_path'])
                    st.success("పోస్ట్ విజయవంతంగా తొలగించబడింది!")
                    st.rerun()

        with st.expander("💬 వ్యాఖ్యలు చూపించు"):
            for _, comment in interactions["comments_df"].iterrows():
                st.markdown(f"""
                    <div style='background-color:#f1f2f6; padding:10px; border-radius:8px; margin-bottom:5px'>
                    <strong>@{comment['username']}</strong>
                    <span style='font-size:11px; color:#636e72'>({comment['timestamp']})</span><br>
                    {comment['content']}
                    </div>
                """, unsafe_allow_html=True)

            new_comment = st.text_input("వ్యాఖ్యను వ్రాయండి...", key=f"comment_input_{post['post_id']}")
            if st.button("సమర్పించు", key=f"submit_comment_{post['post_id']}"):
                if new_comment.strip():
                    record_interaction(post["post_id"], "comment", new_comment.strip())
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

# --- Login / Signup ---
def login_signup():
    mode = st.radio("మోడ్ ఎంచుకోండి", ["లాగిన్", "సైన్ అప్"])
    username = st.text_input("వినియోగదారు పేరు")
    password = st.text_input("పాస్‌వర్డ్", type="password")
    users_df = pd.read_csv(USER_CSV)

    if mode == "లాగిన్":
        if st.button("లాగిన్"):
            if ((users_df['username'] == username) & (users_df['password'] == password)).any():
                st.session_state.logged_in = True
                st.session_state.username = username
                st.stop()
            else:
                st.error("తప్పు లాగిన్ వివరాలు.")
    else:
        if st.button("సైన్ అప్"):
            if username in users_df['username'].values:
                st.error("మీరు ఇప్పటికే నమోదు అయ్యారు. దయచేసి లాగిన్ చేయండి.")
            else:
                new_user = pd.DataFrame([{
                    "username": username,
                    "password": password,
                    "email": "",
                    "about": "",
                    "dob": ""
                }])
                new_user.to_csv(USER_CSV, mode='a', header=False, index=False)
                st.success("సైన్ అప్ విజయవంతం! లాగిన్ చేయండి.")

# --- Main ---
if not st.session_state.logged_in:
    login_signup()
else:
    st.sidebar.title(f"👋 హలో, {st.session_state.username}")
    option = st.sidebar.radio("నావిగేషన్", ["🏠 హోమ్", "➕ కొత్త పోస్ట్", "🔓 లాగ్ అవుట్"])

    if option == "🏠 హోమ్":
        display_posts()

    elif option == "➕ కొత్త పోస్ట్":
        with st.form("new_post_form"):
            caption = st.text_area("మీ సందేశాన్ని వ్రాయండి")
            media = st.file_uploader("మీడియా", type=["jpg", "jpeg", "png", "mp4"])
            submitted = st.form_submit_button("పోస్ట్ చేయండి")

            if submitted and caption.strip():
                post_id = str(uuid.uuid4())
                media_path = ""
                if media:
                    ext = Path(media.name).suffix
                    media_path = str(STORAGE_DIR / f"{post_id}{ext}")
                    with open(media_path, "wb") as f:
                        f.write(media.getbuffer())

                new_post = pd.DataFrame([{
                    "post_id": post_id,
                    "username": st.session_state.username,
                    "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "caption": caption,
                    "media_path": media_path
                }])
                new_post.to_csv(POSTS_CSV, mode="a", header=False, index=False)
                st.success("పోస్ట్ జోడించబడింది!")
                st.rerun()

    elif option == "🔓 లాగ్ అవుట్":
        st.session_state.logged_in = False
        st.session_state.username = None
        st.experimental_rerun()
