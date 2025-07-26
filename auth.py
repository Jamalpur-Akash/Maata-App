import streamlit as st

# Local-only user store (for offline usage)
USERS = {"test": "1234"}

def login_signup():
    tab1, tab2 = st.tabs(["🔐 లాగిన్", "🆕 సైన్అప్"])

    with tab1:
        uname = st.text_input("వినియోగదారుని పేరు")
        pwd = st.text_input("పాస్వర్డ్", type="password")
        if st.button("లాగిన్"):
            if USERS.get(uname) == pwd:
                st.session_state.logged_in = True
                st.session_state.username = uname
            else:
                st.error("తప్పు లాగిన్ వివరాలు")

    with tab2:
        new_user = st.text_input("కొత్త వినియోగదారుని పేరు")
        new_pwd = st.text_input("కొత్త పాస్వర్డ్", type="password")
        if st.button("ఖాతా సృష్టించండి"):
            if new_user in USERS:
                st.warning("ఈ వినియోగదారుని పేరు ముందు నుంచే ఉంది!")
            else:
                USERS[new_user] = new_pwd
                st.success("ఖాతా సృష్టించబడింది! దయచేసి లాగిన్ అవ్వండి.")

with tab1:
    st.markdown("### 🔐 *లాగిన్*")
    # your login form

with tab2:
    st.markdown("### 🆕 *సైన్అప్*")
    # your signup form

