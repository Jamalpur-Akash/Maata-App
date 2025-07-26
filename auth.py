import streamlit as st

USERS = {"test": "1234"}  # Offline dictionary

def login_signup():
    tab1, tab2 = st.tabs(["🔐 లాగిన్", "🆕 ఖాతా సృష్టించండి"])

    with tab1:
        uname = st.text_input("🔑 వినియోగదారుని పేరు (Username)", key="login_username")
        pwd = st.text_input("🔒 పాస్వర్డ్ (Password)", type="password", key="login_password")

        if st.button("లాగిన్"):
            if USERS.get(uname) == pwd:
                st.session_state.logged_in = True
                st.session_state.username = uname
            else:
                st.error("❌ తప్పు లాగిన్ వివరాలు (Invalid credentials)")

    with tab2:
        new_user = st.text_input("👤 కొత్త వినియోగదారుని పేరు (New Username)", key="signup_username")
        new_pwd = st.text_input("🔐 కొత్త పాస్వర్డ్ (New Password)", type="password", key="signup_password")

        if st.button("ఖాతా సృష్టించండి"):
            if new_user in USERS:
                st.warning("⚠ ఈ వినియోగదారు ఇప్పటికే ఉంది! (Username already exists!)")
            else:
                USERS[new_user] = new_pwd
                st.success("✅ ఖాతా సృష్టించబడింది! దయచేసి లాగిన్ అవ్వండి. (Account created! Please login.)")
