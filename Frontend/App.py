import streamlit as st

st.set_page_config(page_title="CampusMind", page_icon="🎓")


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""


def login_page():
    st.title("CampusMind 🎓")
    st.subheader("AI Knowledge Assistant")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        st.write("Login to your account")
        login_username = st.text_input("Username", key="login_user")
        login_password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login"):
            if login_username and login_password:
                st.session_state.logged_in = True
                st.session_state.username = login_username
                st.rerun()
            else:
                st.error("Please enter both username and password.")

    with tab2:
        st.write("Create a new account")
        reg_username = st.text_input("Choose a username", key="reg_user")
        reg_password = st.text_input("Choose a password", type="password", key="reg_pass")

        if st.button("Register"):
            if reg_username and reg_password:
                st.success(f"Account created for {reg_username}! You can now log in.")
            else:
                st.error("Please fill in both fields.")


def chat_page():
    st.title("CampusMind 🎓")
    st.write(f"Welcome, **{st.session_state.username}**!")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    st.divider()
    st.write("Chat interface coming soon...")


if st.session_state.logged_in:
    chat_page()
else:
    login_page()