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
    with st.sidebar:
        st.title("CampusMind 🎓")
        st.write(f"👤 {st.session_state.username}")

        page = st.radio("Navigate", ["💬 Chat", "📄 My Documents", "⚙️ Settings"])

        st.divider()
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()

    if page == "💬 Chat":
        chat_section()
    elif page == "📄 My Documents":
        documents_section()
    elif page == "⚙️ Settings":
        settings_section()


def chat_section():
    st.subheader("Ask a question")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    user_question = st.chat_input("Ask about academic policies, exams, placements...")

    if user_question:
        st.session_state.chat_history.append({"role": "user", "content": user_question})
        with st.chat_message("user"):
            st.write(user_question)

        fake_answer = "This is a placeholder answer. The real AI response will come once the backend RAG pipeline is connected."
        st.session_state.chat_history.append({"role": "assistant", "content": fake_answer})
        with st.chat_message("assistant"):
            st.write(fake_answer)


def documents_section():
    st.subheader("📄 My Documents")

    if "documents" not in st.session_state:
        st.session_state.documents = [
            {"name": "academic_regulations.pdf", "size": "1.2 MB"},
            {"name": "placement_policy.pdf", "size": "850 KB"},
        ]

    uploaded_file = st.file_uploader(
        "Upload a new policy document",
        type=["pdf", "docx", "txt"]
    )
    if uploaded_file is not None:
        st.session_state.documents.append({
            "name": uploaded_file.name,
            "size": f"{round(uploaded_file.size / 1024, 1)} KB"
        })
        st.success(f"'{uploaded_file.name}' added (not yet processed — backend coming soon)")

    st.divider()

    if not st.session_state.documents:
        st.info("No documents uploaded yet.")
    else:
        for i, doc in enumerate(st.session_state.documents):
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.write(f"📄 {doc['name']}")
            col2.write(doc['size'])
            if col3.button("Delete", key=f"delete_{i}"):
                st.session_state.documents.pop(i)
                st.rerun()


def settings_section():
    st.subheader("⚙️ Settings")
    st.write(f"**Username:** {st.session_state.username}")
    st.write("**Account type:** Student")
    st.divider()
    st.write("More settings coming soon (change password, notification preferences, etc.)")


if st.session_state.logged_in:
    chat_page()
else:
    login_page()