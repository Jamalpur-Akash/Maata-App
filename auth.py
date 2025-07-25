import streamlit as st

# Local-only user store (for offline usage)
USERS = {"test": "1234"}

def login_signup():
    tab1, tab2 = st.tabs(["🔐 Login", "🆕 Signup"])

    with tab1:
        uname = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        if st.button("Login"):
            if USERS.get(uname) == pwd:
                st.session_state.logged_in = True
                st.session_state.username = uname
            else:
                st.error("Invalid credentials")

    with tab2:
        new_user = st.text_input("New username")
        new_pwd = st.text_input("New password", type="password")
        if st.button("Create Account"):
            if new_user in USERS:
                st.warning("Username already exists!")
            else:
                USERS[new_user] = new_pwd
                st.success("Account created! Please login.")