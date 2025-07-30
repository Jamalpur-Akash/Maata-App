import streamlit as st
import pandas as pd
import uuid
import os
from pathlib import Path
from deep_translator import GoogleTranslator

st.set_page_config(page_title="Maata - Community", page_icon="🌸", layout="centered")

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

lang_choice = st.selectbox("🌐 Language / భాష / भाषा", ["తెలుగు", "हिन्दी", "English"])
lang_map = {"తెలుగు": "te", "हिन्दी": "hi", "English": "en"}
st.session_state.lang = lang_map[lang_choice]

def t(text):
    lang = st.session_state.get("lang", "te")
    if lang == "te":
        return text
    try:
        return GoogleTranslator(source="te", target=lang).translate(text)
    except:
        return text

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None

st.markdown("<h1 style='text-align:center;'>🌸 మాట ప్రాజెక్ట్</h1>", unsafe_allow_html=True)

def login_signup():
    mode = st.radio(t("మోడ్ ఎంచుకోండి"), [t("లాగిన్"), t("సైన్ అప్")])
    username = st.text_input(t("వినియోగదారు పేరు"))
    password = st.text_input(t("పాస్‌వర్డ్"), type="password")
    users_df = pd.read_csv(USER_CSV)

    if mode == t("లాగిన్"):
        if st.button(t("లాగిన్")):
            if ((users_df['username'] == username) & (users_df['password'] == password)).any():
                st.session_state.logged_in = True
                st.session_state.username = username
                st.stop()
            else:
                st.error(t("తప్పు లాగిన్ వివరాలు."))
    else:
        email = st.text_input(t("ఇమెయిల్"))
        if st.button(t("సైన్ అప్")):
            if username in users_df['username'].values:
                st.error(t("మీరు ఇప్పటికే నమోదు అయ్యారు. దయచేసి లాగిన్ చేయండి."))
            else:
                new_user = pd.DataFrame([{
                    "username": username,
                    "password": password,
                    "email": email,
                    "about": "",
                    "dob": ""
                }])
                new_user.to_csv(USER_CSV, mode='a', header=False, index=False)
                st.success(t("సైన్ అప్ విజయవంతం! లాగిన్ చేయండి."))

def show_profile():
    st.subheader("👤 " + t("మీ ప్రొఫైల్"))
    users_df = pd.read_csv(USER_CSV)
    user_row = users_df[users_df['username'] == st.session_state.username].iloc[0]
    st.image("https://cdn-icons-png.flaticon.com/512/847/847969.png", width=100)
    st.markdown(f"**@{user_row['username']}**")
    st.markdown(f"📧 {user_row['email']}")
    st.markdown(f"📝 {t('మీ గురించి')}: {user_row['about'] or t('లభించలేదు')}")
    st.markdown(f"🎂 {t('పుట్టిన తేది')}: {user_row['dob'] or t('లభించలేదు')}")

    with st.expander("✏️ " + t("వివరాలను సవరించండి")):
        about = st.text_area(t("మీ గురించి"), value=user_row['about'])
        dob = st.date_input(t("పుట్టిన తేది"), value=pd.to_datetime(user_row['dob']) if user_row['dob'] else pd.to_datetime("2000-01-01"))
        if st.button(t("సేవ్ చేయండి")):
            users_df.loc[users_df['username'] == st.session_state.username, 'about'] = about
            users_df.loc[users_df['username'] == st.session_state.username, 'dob'] = str(dob)
            users_df.to_csv(USER_CSV, index=False)
            st.success(t("వివరాలు నవీకరించబడ్డాయి!"))
            st.stop()

def post_section():
    st.header(t("సమాజ పోస్టులు"))
    posts_df = pd.read_csv(POSTS_CSV)
    for _, row in posts_df.iterrows():
        st.markdown(f"**@{row['username']}**")
        st.write(t(row['caption']))
        if row["media_path"] and Path(row["media_path"]).exists():
            st.image(row["media_path"], width=300)
        if row['username'] == st.session_state.username:
            if st.button(t("🗑️ ఈ పోస్ట్‌ను తీసివేయి"), key=row['post_id']):
                posts_df = posts_df[posts_df['post_id'] != row['post_id']]
                posts_df.to_csv(POSTS_CSV, index=False)
                interactions_df = pd.read_csv(INTERACTIONS_CSV)
                interactions_df = interactions_df[interactions_df['post_id'] != row['post_id']]
                interactions_df.to_csv(INTERACTIONS_CSV, index=False)
                if row["media_path"] and Path(row["media_path"]).exists():
                    os.remove(row["media_path"])
                st.success(t("పోస్ట్ తొలగించబడింది"))
                st.stop()

if not st.session_state.logged_in:
    login_signup()
else:
    st.sidebar.title(f"{t('హలో')}, {st.session_state.username}")
    option = st.sidebar.radio(t("నావిగేషన్"), [t("🏠 హోమ్"), t("➕ కొత్త పోస్ట్"), t("👤 ప్రొఫైల్"), t("🔓 లాగ్ అవుట్")])

    if option == t("👤 ప్రొఫైల్"):
        show_profile()
    elif option == t("🔓 లాగ్ అవుట్"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.stop()
    else:
        post_section()
        
