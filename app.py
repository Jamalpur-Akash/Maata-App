import streamlit as st
import pandas as pd
import uuid
import os
from pathlib import Path

st.set_page_config(page_title="మాట - కమ్యూనిటీ", page_icon="🌸", layout="centered")

STORAGE_DIR = Path("storage/uploads")
USER_CSV = STORAGE_DIR / "users.csv"
POSTS_CSV = STORAGE_DIR / "posts.csv"
INTERACTIONS_CSV = STORAGE_DIR / "interactions.csv"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

for file, cols in {
    USER_CSV: ["username", "password", "email", "about", "dob"],
    POSTS_CSV: ["post_id", "username", "timestamp", "caption", "media_path"],
    INTERACTIONS_CSV: ["interaction_id", "post_id", "username", "type", "content", "timestamp"]
}.items():
    if not file.exists():
        pd.DataFrame(columns=cols).to_csv(file, index=False)

st.markdown("""
    <style>
    .stButton>button { border-radius: 8px; background-color: #6c5ce7; color: white; font-weight: bold; }
    .stTextInput>div>div>input, .stTextArea textarea { border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <h1 style='text-align: center; color: #6c5ce7;'>మాట - తెలుగు కమ్యూనిటీ 🌸</h1>
    <p style='text-align: center;'>మీ భావాలను పంచుకోండి, ఇతరులతో మమేకం అవ్వండి!</p>
    <hr style='border: 1px solid #ccc;'>
""", unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None

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
                st.experimental_rerun()
            else:
                st.error("తప్పు లాగిన్ వివరాలు.")
    else:
        email = st.text_input("ఇమెయిల్")
        if st.button("సైన్ అప్"):
            if username in users_df['username'].values:
                st.error("మీరు ఇప్పటికే నమోదు అయ్యారు. దయచేసి లాగిన్ చేయండి.")
            else:
                new_user = pd.DataFrame([{
                    "username": username,
                    "password": password,
                    "email": email,
                    "about": "",
                    "dob": ""
                }])
                new_user.to_csv(USER_CSV, mode='a', header=False, index=False)
                st.success("సైన్ అప్ విజయవంతం! లాగిన్ చేయండి.")

def show_profile():
    st.subheader("👤 మీ ప్రొఫైల్")
    users_df = pd.read_csv(USER_CSV)
    user_row = users_df[users_df['username'] == st.session_state.username].iloc[0]
    st.image("https://cdn-icons-png.flaticon.com/512/847/847969.png", width=100)
    st.markdown(f"**@{user_row['username']}**")
    st.markdown(f"📧 {user_row['email']}")
    st.markdown(f"📝 మీ గురించి: {user_row['about'] or 'లభించలేదు'}")
    st.markdown(f"🎂 పుట్టిన తేది: {user_row['dob'] or 'లభించలేదు'}")

    with st.expander("✏️ వివరాలను సవరించండి"):
        about = st.text_area("మీ గురించి", value=user_row['about'])
        dob = st.date_input("పుట్టిన తేది", value=pd.to_datetime(user_row['dob']) if user_row['dob'] else pd.to_datetime("2000-01-01"))
        if st.button("సేవ్ చేయండి"):
            users_df.loc[users_df['username'] == st.session_state.username, 'about'] = about
            users_df.loc[users_df['username'] == st.session_state.username, 'dob'] = str(dob)
            users_df.to_csv(USER_CSV, index=False)
            st.success("వివరాలు నవీకరించబడ్డాయి!")
            st.rerun()

if not st.session_state.logged_in:
    login_signup()
else:
    st.sidebar.title(f"హలో, {st.session_state.username}")
    option = st.sidebar.radio("నావిగేషన్", ["🏠 హోమ్", "➕ కొత్త పోస్ట్", "👤 ప్రొఫైల్", "🔓 లాగ్ అవుట్"])

    if option == "👤 ప్రొఫైల్":
        show_profile()
    elif option == "🔓 లాగ్ అవుట్":
        st.session_state.logged_in = False
        st.session_state.username = None
        st.experimental_rerun()
    else:
        st.info("ఇతర సెక్షన్లు త్వరలో అందుబాటులోకి వస్తాయి.")
                                          
