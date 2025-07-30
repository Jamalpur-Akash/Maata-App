import streamlit as st
import pandas as pd
import uuid
import os
from datetime import datetime
import pytz
from pathlib import Path
from deep_translator import GoogleTranslator

# Setup
st.set_page_config(page_title="మాట - కమ్యూనిటీ", page_icon="🌸", layout="centered")

STORAGE_DIR = Path("storage/uploads")
USER_CSV = STORAGE_DIR / "users.csv"
POSTS_CSV = STORAGE_DIR / "posts.csv"
INTERACTIONS_CSV = STORAGE_DIR / "interactions.csv"
COMMENTS_CSV = STORAGE_DIR / "comments.csv"

STORAGE_DIR.mkdir(parents=True, exist_ok=True)
for file, columns in [(USER_CSV, ["username", "password", "email", "about", "dob"]),
                      (POSTS_CSV, ["post_id", "username", "timestamp", "caption", "media_path"]),
                      (INTERACTIONS_CSV, ["post_id", "username", "action"]),
                      (COMMENTS_CSV, ["post_id", "username", "comment", "timestamp"])]:
    if not file.exists():
        pd.DataFrame(columns=columns).to_csv(file, index=False)

# Language Mapping
LANG_MAP = {"తెలుగు": "te", "हिन्दी": "hi", "English": "en"}
if "lang" not in st.session_state:
    st.session_state.lang = "తెలుగు"

lang_choice = st.selectbox("🌐 Language / భాష / भाषा", list(LANG_MAP.keys()), key="lang_choice")
st.session_state.lang = lang_choice
lang_code = LANG_MAP[st.session_state.lang]

def t(te, hi, en):
    return {"తెలుగు": te, "हिन्दी": hi, "English": en}[st.session_state.lang]

def translate_text(text):
    try:
        return GoogleTranslator(source='auto', target=lang_code).translate(text)
    except:
        return text

def load_csv(path): return pd.read_csv(path) if path.exists() else pd.DataFrame()

def save_post(username, caption, media_file):
    df = load_csv(POSTS_CSV)
    ts = datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S %Z")
    media_path = ""
    if media_file:
        ext = Path(media_file.name).suffix
        media_filename = f"{uuid.uuid4().hex}{ext}"
        media_path = str(STORAGE_DIR / media_filename)
        with open(media_path, "wb") as f:
            f.write(media_file.getbuffer())
    df.loc[len(df)] = [str(uuid.uuid4()), username, ts, caption or "", media_path]
    df.to_csv(POSTS_CSV, index=False)

def delete_post(post_id):
    df = load_csv(POSTS_CSV)
    df = df[df["post_id"] != post_id]
    df.to_csv(POSTS_CSV, index=False)

def like_post(post_id, user):
    df = load_csv(INTERACTIONS_CSV)
    if df[(df.post_id == post_id) & (df.username == user) & (df.action == "like")].empty:
        df.loc[len(df)] = [post_id, user, "like"]
        df.to_csv(INTERACTIONS_CSV, index=False)

def count_likes(post_id):
    df = load_csv(INTERACTIONS_CSV)
    if "post_id" not in df.columns or df.empty:
        return 0
    df["post_id"] = df["post_id"].astype(str)
    return len(df[(df["post_id"] == post_id) & (df["action"] == "like")])


def add_comment(post_id, username, comment):
    df = load_csv(COMMENTS_CSV)
    ts = datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S %Z")
    df.loc[len(df)] = [post_id, username, comment, ts]
    df.to_csv(COMMENTS_CSV, index=False)

def get_comments(post_id):
    df = load_csv(COMMENTS_CSV)
    return df[df.post_id == post_id]

# Login / Signup
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

def login_signup():
    st.header(t("మాట కమ్యూనిటీ", "माटा कम्युनिटी", "Maata Community"))
    choice = st.radio("", [t("పైన", "ऊपर", "Login"), t("సైన్ అప్", "रजिस्टर", "Sign up")])
    df_users = load_csv(USER_CSV)

    if choice == t("పైన", "ऊपर", "Login"):
        u = st.text_input(t("వినియోగదారు పేరు", "उपयोगकर्ता नाम", "Username"))
        p = st.text_input(t("పాస్వర్డ్", "पासवर्ड", "Password"), type="password")
        if st.button(t("లాగిన్", "लॉग इन", "Login")):
            if not df_users[(df_users.username == u) & (df_users.password == p)].empty:
                st.session_state.logged_in = True
                st.session_state.username = u
                st.experimental_rerun()
            else:
                st.error(t("తప్పుడు వ్యక్తీకరణ", "गलत क्रेडेंशियल", "Incorrect credentials"))
    else:
        u = st.text_input(t("వినియోగదారు పేరు", "उपयोगकर्ता नाम", "Username"))
        e = st.text_input("Email")
        p = st.text_input(t("పాస్వర్డ్", "पासवर्ड", "Password"), type="password")
        pc = st.text_input(t("నిర్ధారించు పాస్‌వర్డ్", "पासवर्ड पुनः दर्ज करें", "Confirm Password"), type="password")
        if st.button(t("సైన్ అప్", "रजिस्टर", "Sign up")):
            if u in df_users.username.values:
                st.warning(t("మీరు ఇప్పటికే నమోదు అయ్యారు", "आप पहले से रजिस्टर्ड हैं", "You are already registered"))
            elif p != pc:
                st.error(t("పాస్‌వర్డ్‌లు సరిపోలేదు", "पासवर्ड मेल नहीं खाते", "Passwords do not match"))
            else:
                df_users.loc[len(df_users)] = {"username": u, "password": p, "email": e, "about": "", "dob": ""}
                df_users.to_csv(USER_CSV, index=False)
                st.success(t("నమోదు విజయవంతం!", "रजिस्टर सफल!", "Registration successful!"))

if not st.session_state.logged_in:
    login_signup()
else:
    st.sidebar.title(f"{t('హలో','नमस्ते','Hello')}, {st.session_state.username}")
    nav = st.sidebar.radio(t("నావిగేషన్", "नेविगेशन", "Navigation"),
        [t("హోమ్", "होम", "Home"), t("కొత్త పోస్ట్", "नई पोस्ट", "New Post"),
         t("ప్రొఫైల్", "प्रोफ़ाइल", "Profile"), t("లాగ్ అవుట్", "लॉग आउट", "Logout")])

    if nav == t("లాగ్ అవుట్", "लॉग आउट", "Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.experimental_rerun()

    elif nav == t("ప్రొఫైల్", "प्रोफ़ाइल", "Profile"):
        st.header(t("ప్రొఫైల్", "प्रोफ़ाइल", "Profile"))
        u = st.session_state.username
        df = load_csv(USER_CSV)
        row = df[df.username == u].iloc[0]
        st.image("https://cdn-icons-png.flaticon.com/512/847/847969.png", width=100)
        st.write(f"**{t('వినియోగదారు పేరు','उपयोगकर्ता नाम','Username')}:** {row.username}")
        st.write(f"**Email:** {row.email}")
        st.write(f"**{t('నా గురించి','मेरे बारे में','About')}:** {row.about or t('లభించలేదు','उपलब्ध नहीं','Not available')}")
        st.write(f"**{t('పుట్టిన తేదీ','जन्म तिथि','Date of Birth')}:** {row.dob or t('లభించలేదు','उपलब्ध नहीं','Not available')}")

    elif nav == t("కొత్త పోస్ట్", "नई पोस्ट", "New Post"):
        st.header(t("కొత్త పోస్ట్", "नई पोस्ट", "New Post"))
        caption = st.text_area(t("ఈ రోజు ఏమైంది మీకెంతో మాట్లాడండి...", "आज क्या है साझा करें...", "Share what's happening..."))
        media = st.file_uploader(t("మీడియా జోడించండి", "मीडिया जोड़ें", "Add Media"), type=["png", "jpg", "jpeg", "mp4"])
        if st.button(t("పోస్ట్", "पोस्ट करें", "Post")):
            save_post(st.session_state.username, caption, media)
            st.success(t("పోస్ట్ విజయవంతంగా పంపబడింది", "पोस्ट सफलतापूर्वक भेजी गई", "Post successfully shared"))
            st.experimental_rerun()

    else:
        st.header("📢 " + t("పోస్టులు", "पोस्ट्स", "Posts"))
        dfp = load_csv(POSTS_CSV).sort_values(by="timestamp", ascending=False)
        for _, r in dfp.iterrows():
            post_id, uname, ts, cap, media_path = r["post_id"], r["username"], r["timestamp"], r["caption"], r["media_path"]
            st.markdown(f"**@{uname}** _{ts}_")
            st.write(translate_text(cap))
            if media_path and Path(media_path).exists():
                st.image(media_path, use_container_width=True)
            if st.button("👍 " + t("ఇష్టం","पसंद","Like"), key=f"like_{post_id}"):
                like_post(post_id, st.session_state.username)
            st.caption(f"{count_likes(post_id)} {t('లైక్స్','लाईक','likes')}")

            comment = st.text_input(f"{t('వ్యాఖ్య','टिप्पणी','Comment')} - {post_id}", key=f"comment_{post_id}")
            if st.button(t("కామెంట్","टिप्पणी करें","Comment"), key=f"comment_btn_{post_id}"):
                add_comment(post_id, st.session_state.username, comment)
                st.experimental_rerun()
            for _, c in get_comments(post_id).iterrows():
                st.write(f"- **{c.username}**: {translate_text(c.comment)}")

            if uname == st.session_state.username:
                if st.button(t("తొలగించండి", "हटाएं", "Delete"), key=f"del_{post_id}"):
                    delete_post(post_id)
                    st.success(t("పోస్ట్ తొలగించబడింది", "पोस्ट हटायी गई", "Post deleted"))
                    st.experimental_rerun()
            st.markdown("---")
    
