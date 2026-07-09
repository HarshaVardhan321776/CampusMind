import streamlit as st

st.set_page_config(page_title="CampusMind", page_icon="🎓")
# Theme toggle - stored in session_state so it persists across reruns
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

col1, col2 = st.columns([6, 1])
with col2:
    toggle = st.toggle("🌙", value=(st.session_state.theme == "dark"))
    st.session_state.theme = "dark" if toggle else "light"

if st.session_state.theme == "dark":
    bg, card, text, subtext, accent, accent_text, border = (
        "#12172B", "#1B2340", "#EDEFF5", "#9AA3BC", "#D4A24C", "#12172B", "#2A3358"
    )
else:
    bg, card, text, subtext, accent, accent_text, border = (
        "#F7F4EC", "#FFFFFF", "#1B2340", "#5C6178", "#B8863E", "#FFFFFF", "#E3DCC8"
    )

st.markdown(f"""
<style>
    .stApp {{
        background-color: {bg};
        color: {text};
    }}
    h1, h2, h3 {{
        font-family: 'Georgia', 'Times New Roman', serif;
        color: {text} !important;
        letter-spacing: 0.3px;
    }}
    h1 {{
        border-bottom: 2px solid {accent};
        padding-bottom: 10px;
    }}
    p, label, .stMarkdown, span {{
        color: {text} !important;
    }}
    [data-testid="stSidebar"] {{
        background-color: {card};
        border-right: 1px solid {border};
    }}
    [data-testid="stSidebar"] * {{
        color: {text} !important;
    }}
    .stButton button {{
        background-color: {accent};
        color: {accent_text};
        border: none;
        border-radius: 6px;
        font-weight: 600;
        padding: 0.5rem 1.2rem;
    }}
    .stTextInput input {{
        background-color: {card};
        color: {text};
        border: 1px solid {border};
        border-radius: 6px;
    }}
    .stChatMessage {{
        background-color: {card};
        border-radius: 10px;
        border: 1px solid {border};
    }}
    .stTabs [data-baseweb="tab"] {{
        color: {subtext};
    }}
    .stTabs [aria-selected="true"] {{
        color: {accent} !important;
        border-bottom: 2px solid {accent};
    }}
    .stRadio label {{
        color: {text} !important;
    }}
    .stAlert {{
        background-color: {card};
        color: {text};
        border-radius: 8px;
    }}
    /* File uploader - covering multiple possible internal structures */
    [data-testid="stFileUploader"] section {{
        background-color: {card} !important;
        border: 1px dashed {border} !important;
    }}
    [data-testid="stFileUploader"] section > div {{
        background-color: {card} !important;
    }}
    [data-testid="stFileUploaderDropzone"] {{
        background-color: {card} !important;
        border: 1px dashed {border} !important;
    }}
    [data-testid="stFileUploader"] * {{
        color: {text} !important;
    }}
    [data-testid="stFileUploader"] button {{
        background-color: {bg} !important;
        color: {text} !important;
        border: 1px solid {border} !important;
    }}
</style>
""", unsafe_allow_html=True)


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

if "app_loaded" not in st.session_state:
    st.session_state.app_loaded = False

if not st.session_state.app_loaded:
    splash = st.empty()
    with splash.container():
        st.markdown(f"""
        <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:70vh;">
            <div style="font-size:64px; margin-bottom:10px;">🎓</div>
            <div style="font-family:'Georgia', serif; font-size:32px; color:{text}; letter-spacing:1px;">
                CampusMind
            </div>
            <div style="color:{subtext}; margin-top:8px; font-size:14px;">
                Opening your knowledge base...
            </div>
        </div>
        """, unsafe_allow_html=True)

        progress_bar = st.progress(0)
        import time
        for pct in range(0, 101, 5):
            time.sleep(0.03)
            progress_bar.progress(pct)

    st.session_state.app_loaded = True
    splash.empty()
    st.rerun()
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

    with st.sidebar:
        st.header("📄 Your Documents")
        uploaded_file = st.file_uploader(
            "Upload a policy document",
            type=["pdf", "docx", "txt"]
        )
        if uploaded_file is not None:
            st.success(f"'{uploaded_file.name}' selected (not yet processed — backend coming soon)")

        st.divider()
        st.write("**Uploaded so far:**")

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

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                import time
                time.sleep(1.2)  
                fake_answer = "This is a placeholder answer. The real AI response will come once the backend RAG pipeline is connected."
            st.write(fake_answer)

        st.session_state.chat_history.append({"role": "assistant", "content": fake_answer})

if st.session_state.logged_in:
    chat_page()
else:
    login_page()