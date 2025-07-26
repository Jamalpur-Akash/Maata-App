import streamlit as st

# Local-only user store (for offline usage)
USERS = {"test": "1234"}

def login_signup():
    tab1, tab2 = st.tabs(["🔐 **లాగిన్**", "🆕 **సైన్అప్**"])

    with tab1:
        # Username
        st.markdown("<label style='font-weight: bold; margin-top: 2px;'>వినియోగదారుని పేరు</label>", unsafe_allow_html=True)
        uname = st.text_input("", key="username")

        # Small spacer
        st.markdown("<div style='margin-top: 2px;'></div>", unsafe_allow_html=True)

        # Password
        st.markdown("<label style='font-weight: bold; margin-top: 2px;'>పాస్వర్డ్</label>", unsafe_allow_html=True)
        pwd = st.text_input("", type="password", key="password")

        if st.button("లాగిన్"):
            if USERS.get(uname) == pwd:
                st.session_state.logged_in = True
                st.session_state.username = uname
            else:
                st.error("తప్పు లాగిన్ వివరాలు")

    with tab2:
        st.markdown("### 🆕 *సైన్అప్*")
        new_user = st.text_input("**కొత్త వినియోగదారుని పేరు**")
        new_pwd = st.text_input("**కొత్త పాస్వర్డ్**", type="password")
        if st.button("ఖాతా సృష్టించండి"):
            if new_user in USERS:
                st.warning("ఈ వినియోగదారుని పేరు ముందు నుంచే ఉంది!")
            else:
                USERS[new_user] = new_pwd
                st.success("ఖాతా సృష్టించబడింది! దయచేసి లాగిన్ అవ్వండి.")
