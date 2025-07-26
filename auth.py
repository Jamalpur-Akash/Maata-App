import streamlit as st

USERS = {"test": "1234"}  # Offline dictionary

def login_signup():
    tab1, tab2 = st.tabs(["🔐 లాగిన్", "🆕 ఖాతా సృష్టించండి"])

    with tab1:
        
# Inject CSS to control spacing
        st.markdown("""
            <style>
               .custom-label {
                margin-bottom: 2px;
                font-weight: bold;
                }
               .custom-input > div {
                margin-top: 0px !important;
                  }
                </style>
              """, unsafe_allow_html=True)

# Display label using markdown and style class
           st.markdown('<div class="custom-label">కొత్త వినియోగదారుని పేరు (New Username)</div>', unsafe_allow_html=True)
       with st.container():
          st.markdown('<div class="custom-input">', unsafe_allow_html=True)
          username = st.text_input('', key="username")  # empty label avoids extra space
          st.markdown('</div>', unsafe_allow_html=True)
       """ st.markdown("**🔑 వినియోగదారుని పేరు (Username)**", unsafe_allow_html=True)
        uname = st.text_input("", key="login_username")

        st.markdown("**🔒 పాస్వర్డ్ (Password)**", unsafe_allow_html=True)
        pwd = st.text_input("", type="password", key="login_password")

        if st.button("లాగిన్"):
            if USERS.get(uname) == pwd:
                st.session_state.logged_in = True
                st.session_state.username = uname
            else:
                st.error("❌ తప్పు లాగిన్ వివరాలు (Invalid credentials)")"""

    with tab2:
        st.markdown("**👤 కొత్త వినియోగదారుని పేరు (New Username)**", unsafe_allow_html=True)
        new_user = st.text_input("", key="signup_username")

        st.markdown("**🔐 కొత్త పాస్వర్డ్ (New Password)**", unsafe_allow_html=True)
        new_pwd = st.text_input("", type="password", key="signup_password")

        if st.button("ఖాతా సృష్టించండి"):
            if new_user in USERS:
                st.warning("⚠️ ఈ వినియోగదారు ఇప్పటికే ఉంది! (Username already exists!)")
            else:
                USERS[new_user] = new_pwd
                st.success("✅ ఖాతా సృష్టించబడింది! దయచేసి లాగిన్ అవ్వండి. (Account created! Please login.)")
