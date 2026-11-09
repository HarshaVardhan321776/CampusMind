import streamlit as st
import requests
import time
import os
from datetime import datetime

# ==============================================================================
# 1. APPLICATION & PAGE CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="CampusMind | Academic AI Assistant",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

DEFAULT_API_URL = os.environ.get("CAMPUSMIND_API_URL", "http://127.0.0.1:8000")


def strip_auth_token_from_url() -> bool:
    """Remove JWT token from the URL to prevent session hijacking on shared links."""
    if "token" in st.query_params:
        del st.query_params["token"]
        return True
    return False


# State Initialization
if "backend_url" not in st.session_state:
    st.session_state.backend_url = DEFAULT_API_URL
if "theme" not in st.session_state:
    st.session_state.theme = "light"
if "auth_notice" not in st.session_state:
    st.session_state.auth_notice = None
if "token" not in st.session_state:
    st.session_state.token = None
if strip_auth_token_from_url():
    st.session_state.auth_notice = (
        "This link included a sign-in token. For your security, please sign in with your own account."
    )
    st.session_state.token = None
    st.session_state.user = None
if "user" not in st.session_state:
    st.session_state.user = None
if "current_conversation_id" not in st.session_state:
    st.session_state.current_conversation_id = None
if "current_conversation_title" not in st.session_state:
    st.session_state.current_conversation_title = "New Research Thread"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversations" not in st.session_state:
    st.session_state.conversations = []
if "page" not in st.session_state:
    st.session_state.page = "dashboard"
if "user_docs" not in st.session_state:
    st.session_state.user_docs = []
if "suggested_prompt" not in st.session_state:
    st.session_state.suggested_prompt = None


# ==============================================================================
# 2. OFFICIAL CAMPUSMIND BRAND DESIGN SYSTEM & TYPOGRAPHY
# ==============================================================================
# Primary Brand Colors:
# - Powder Blue: #B9DDF5
# - Pure White: #FFFFFF
# - Vibrant Racing Orange: #FF5A1F
# Supporting Neutrals:
# - Deep Navy / Charcoal: #0F1E36 (Primary text)
# - Muted Slate: #475569 (Secondary text)
# - Neutral Slate: #64748B (Captions/meta)
# - Neutral Grey Border: #D8E2EC
# - Subtle Section Background: #F0F7FD

is_dark = (st.session_state.theme == "dark")

if is_dark:
    THEME = {
        "bg": "#0B121E",
        "canvas": "#0F1726",
        "surface": "#131E30",
        "surface_subtle": "#18263D",
        "surface_hover": "#1E2F4A",
        "border": "#22334D",
        "border_subtle": "#19273C",
        "text_primary": "#FFFFFF",
        "text_secondary": "#B9DDF5",
        "text_muted": "#8297AF",
        "powder_blue": "#B9DDF5",
        "powder_blue_tint": "rgba(185, 221, 245, 0.12)",
        "powder_blue_text": "#B9DDF5",
        "accent": "#FF5A1F",
        "accent_hover": "#E04E18",
        "accent_text": "#FFFFFF",
        "success": "#10B981",
        "success_bg": "rgba(16, 185, 129, 0.12)",
        "danger": "#EF4444",
        "danger_bg": "rgba(239, 68, 68, 0.12)",
        "card_shadow": "0 1px 3px rgba(0, 0, 0, 0.2)",
    }
else:
    THEME = {
        "bg": "#FFFFFF",
        "canvas": "#F8FAFC",
        "surface": "#FFFFFF",
        "surface_subtle": "#F0F7FD",
        "surface_hover": "#E9F3FB",
        "border": "#D8E2EC",
        "border_subtle": "#EBF2F7",
        "text_primary": "#0F1E36",
        "text_secondary": "#475569",
        "text_muted": "#64748B",
        "powder_blue": "#B9DDF5",
        "powder_blue_tint": "#F0F7FD",
        "powder_blue_text": "#1A5B87",
        "accent": "#FF5A1F",
        "accent_hover": "#E04E18",
        "accent_text": "#FFFFFF",
        "success": "#0D7A53",
        "success_bg": "#EDF7F2",
        "danger": "#C53030",
        "danger_bg": "#FDF2F2",
        "card_shadow": "0 1px 3px rgba(15, 30, 54, 0.05)",
    }

st.markdown(f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:ital,wght@0,400;0,500;0,600;1,400&family=Public+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400;1,8..60,600&display=swap" rel="stylesheet">
<style>
    /* Global Typography Reset */
    html, body, [class*="css"] {{
        font-family: 'Public Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        letter-spacing: -0.01em;
    }}
    
    .stApp {{
        background-color: {THEME['bg']} !important;
        color: {THEME['text_primary']} !important;
    }}
    
    /* Academic Typography Hierarchy */
    h1, h2, h3, h4,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] h4 {{
        font-family: 'Source Serif 4', Georgia, serif !important;
        font-weight: 600 !important;
        color: {THEME['text_primary']} !important;
        letter-spacing: -0.015em !important;
        margin-top: 0 !important;
    }}
    
    p, span, label,
    div[data-testid="stMarkdownContainer"] p, 
    [data-testid="stMarkdownContainer"] li, 
    [data-testid="stMarkdownContainer"] span {{
        color: {THEME['text_primary']} !important;
        line-height: 1.6;
    }}
    
    [data-testid="stMarkdownContainer"] strong, 
    [data-testid="stMarkdownContainer"] b {{
        color: {THEME['text_primary']} !important;
        font-weight: 600 !important;
    }}
    
    [data-testid="stMarkdownContainer"] em, 
    [data-testid="stMarkdownContainer"] i {{
        color: {THEME['text_secondary']} !important;
    }}

    a {{
        color: {THEME['accent']} !important;
        text-decoration: underline;
        font-weight: 500;
    }}
    
    /* Header Bar */
    header[data-testid="stHeader"] {{
        background-color: {THEME['bg']} !important;
        border-bottom: 1px solid {THEME['border_subtle']} !important;
    }}
    header[data-testid="stHeader"] * {{
        background-color: transparent !important;
    }}
    div[data-testid="stToolbar"] {{
        background-color: transparent !important;
    }}
    
    /* Structured Sidebar (No Liquid Glass) */
    [data-testid="stSidebar"],
    section[data-testid="stSidebar"] {{
        background-color: {THEME['canvas']} !important;
        border-right: 1px solid {THEME['border']} !important;
        box-shadow: none !important;
    }}
    [data-testid="stSidebar"] > div:first-child,
    [data-testid="stSidebarContent"],
    [data-testid="stSidebarUserContent"] {{
        background-color: transparent !important;
    }}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p, 
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span {{
        color: {THEME['text_primary']} !important;
    }}

    /* Sidebar Brand Element */
    .brand-mark {{
        font-family: 'Source Serif 4', Georgia, serif;
        font-size: 1.35rem;
        font-weight: 700;
        color: {THEME['text_primary']};
        display: flex;
        align-items: center;
        gap: 8px;
        letter-spacing: -0.02em;
    }}
    .brand-dot {{
        width: 8px;
        height: 8px;
        background-color: {THEME['accent']};
        border-radius: 2px;
        display: inline-block;
    }}
    
    /* Academic Cards (No liquid glass, no left-side stripes) */
    .academic-card {{
        background-color: {THEME['surface']} !important;
        border: 1px solid {THEME['border']} !important;
        border-radius: 8px;
        padding: 1.35rem 1.6rem;
        box-shadow: {THEME['card_shadow']};
        margin-bottom: 1.25rem;
    }}

    .academic-card-subtle {{
        background-color: {THEME['surface_subtle']} !important;
        border: 1px solid {THEME['border']} !important;
        border-radius: 8px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1.25rem;
    }}
    
    /* Typographic Badges */
    .academic-badge {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.76rem;
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 500;
        padding: 3px 8px;
        border-radius: 4px;
        margin-right: 6px;
    }}
    .badge-powder {{
        background-color: {THEME['powder_blue_tint']};
        color: {THEME['powder_blue_text']} !important;
        border: 1px solid {THEME['powder_blue']};
    }}
    .badge-status-online {{
        background-color: {THEME['success_bg']};
        color: {THEME['success']} !important;
        border: 1px solid {THEME['success']};
    }}
    .badge-status-offline {{
        background-color: {THEME['danger_bg']};
        color: {THEME['danger']} !important;
        border: 1px solid {THEME['danger']};
    }}
    .badge-meta {{
        background-color: {THEME['surface_subtle']};
        color: {THEME['text_muted']} !important;
        border: 1px solid {THEME['border']};
    }}
    
    /* Primary Action Buttons (Solid Vibrant Racing Orange) */
    .stButton > button,
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="baseButton-primary"],
    div[data-testid="stFormSubmitButton"] > button {{
        background-color: {THEME['accent']} !important;
        background-image: none !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border: 1px solid {THEME['accent']} !important;
        border-radius: 6px !important;
        font-family: 'Public Sans', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        padding: 0.55rem 1.2rem !important;
        box-shadow: none !important;
        min-height: 38px !important;
        white-space: nowrap !important;
        transition: background-color 0.15s ease, border-color 0.15s ease !important;
    }}
    
    .stButton > button:not([kind="secondary"]):not([data-testid="baseButton-secondary"]) *,
    .stButton > button[kind="primary"] *,
    .stButton > button[data-testid="baseButton-primary"] *,
    div[data-testid="stFormSubmitButton"] > button * {{
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 600 !important;
    }}
    
    .stButton > button:hover {{
        background-color: {THEME['accent_hover']} !important;
        border-color: {THEME['accent_hover']} !important;
    }}
    
    /* Secondary Buttons (Structured White with Border) */
    .stButton > button[kind="secondary"],
    .stButton > button[data-testid="baseButton-secondary"] {{
        background-color: {THEME['surface']} !important;
        background-image: none !important;
        color: {THEME['text_primary']} !important;
        -webkit-text-fill-color: {THEME['text_primary']} !important;
        border: 1px solid {THEME['border']} !important;
        border-radius: 6px !important;
        box-shadow: none !important;
        font-family: 'Public Sans', sans-serif !important;
        font-weight: 500 !important;
        min-height: 38px !important;
        transition: background-color 0.15s ease, border-color 0.15s ease !important;
    }}
    
    .stButton > button[kind="secondary"] *,
    .stButton > button[data-testid="baseButton-secondary"] * {{
        color: {THEME['text_primary']} !important;
        -webkit-text-fill-color: {THEME['text_primary']} !important;
        font-weight: 500 !important;
    }}
    
    .stButton > button[kind="secondary"]:hover,
    .stButton > button[data-testid="baseButton-secondary"]:hover {{
        background-color: {THEME['surface_subtle']} !important;
        border-color: {THEME['powder_blue']} !important;
    }}
    .stButton > button[kind="secondary"]:hover *,
    .stButton > button[data-testid="baseButton-secondary"]:hover * {{
        color: {THEME['text_primary']} !important;
        -webkit-text-fill-color: {THEME['text_primary']} !important;
    }}
    
    /* Form Inputs & Selectboxes */
    .stTextInput > div,
    .stTextInput > div > div,
    div[data-baseweb="input"],
    div[data-baseweb="input"] > div,
    div[data-baseweb="base-input"],
    .stSelectbox > div,
    .stSelectbox > div > div,
    div[data-baseweb="select"],
    div[data-baseweb="select"] > div {{
        background-color: {THEME['surface']} !important;
        color: {THEME['text_primary']} !important;
        -webkit-text-fill-color: {THEME['text_primary']} !important;
        border: 1px solid {THEME['border']} !important;
        border-radius: 6px !important;
        box-shadow: none !important;
    }}
    
    .stTextInput input,
    .stSelectbox input {{
        background-color: transparent !important;
        color: {THEME['text_primary']} !important;
        -webkit-text-fill-color: {THEME['text_primary']} !important;
        font-family: 'Public Sans', sans-serif !important;
        font-size: 0.9rem !important;
        padding: 0.5rem 0.75rem !important;
    }}
    
    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="select"]:focus-within {{
        border-color: {THEME['powder_blue']} !important;
        box-shadow: 0 0 0 2px rgba(185, 221, 245, 0.5) !important;
    }}
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {{
        border-bottom: 1px solid {THEME['border']};
        gap: 6px;
    }}
    .stTabs [data-baseweb="tab"] {{
        color: {THEME['text_secondary']} !important;
        border-radius: 4px 4px 0 0;
        padding: 8px 16px;
        font-size: 0.88rem;
        font-weight: 500;
        background-color: transparent !important;
    }}
    .stTabs [data-baseweb="tab"] * {{
        color: {THEME['text_secondary']} !important;
    }}
    .stTabs [aria-selected="true"] {{
        color: {THEME['text_primary']} !important;
        font-weight: 600 !important;
        border-bottom: 2px solid {THEME['accent']} !important;
        background-color: transparent !important;
    }}
    .stTabs [aria-selected="true"] * {{
        color: {THEME['text_primary']} !important;
    }}
    
    /* Chat Messages */
    [data-testid="stChatMessage"] {{
        background-color: {THEME['surface']} !important;
        border: 1px solid {THEME['border']} !important;
        border-radius: 6px !important;
        padding: 1.1rem 1.4rem !important;
        margin-bottom: 0.9rem !important;
        box-shadow: {THEME['card_shadow']};
    }}
    [data-testid="stChatMessage"] p, 
    [data-testid="stChatMessage"] span, 
    [data-testid="stChatMessage"] li, 
    [data-testid="stChatMessage"] div {{
        color: {THEME['text_primary']} !important;
    }}
    
    /* Tables */
    table {{
        background-color: {THEME['surface']} !important;
        color: {THEME['text_primary']} !important;
        border-collapse: collapse !important;
        border: 1px solid {THEME['border']} !important;
        width: 100% !important;
        margin: 12px 0 !important;
        border-radius: 4px !important;
    }}
    th {{
        background-color: {THEME['surface_subtle']} !important;
        color: {THEME['text_primary']} !important;
        font-family: 'Public Sans', sans-serif !important;
        font-weight: 600 !important;
        border: 1px solid {THEME['border']} !important;
        padding: 8px 12px !important;
        text-align: left !important;
        font-size: 0.84rem !important;
    }}
    td {{
        color: {THEME['text_primary']} !important;
        border: 1px solid {THEME['border']} !important;
        padding: 8px 12px !important;
        font-size: 0.86rem !important;
    }}
    
    /* Code & Technical Content */
    code:not(.academic-badge) {{
        background-color: {THEME['surface_subtle']} !important;
        color: {THEME['text_primary']} !important;
        padding: 2px 5px !important;
        border-radius: 3px !important;
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: 0.84em !important;
        border: 1px solid {THEME['border_subtle']} !important;
    }}
    pre {{
        background-color: {THEME['surface_subtle']} !important;
        border: 1px solid {THEME['border']} !important;
        border-radius: 6px !important;
        padding: 12px !important;
    }}
    pre code {{
        color: {THEME['text_primary']} !important;
        background-color: transparent !important;
        border: none !important;
    }}
    
    /* Chat Input Bar */
    [data-testid="stChatInput"] {{
        background-color: {THEME['bg']} !important;
        border-top: 1px solid {THEME['border']} !important;
    }}
    [data-testid="stChatInput"] > div {{
        background-color: {THEME['surface']} !important;
        border: 1px solid {THEME['border']} !important;
        border-radius: 6px !important;
    }}
    [data-testid="stChatInput"] > div:focus-within {{
        border-color: {THEME['powder_blue']} !important;
        box-shadow: 0 0 0 2px rgba(185, 221, 245, 0.45) !important;
    }}
    [data-testid="stChatInput"] button svg {{
        fill: {THEME['accent']} !important;
        stroke: {THEME['accent']} !important;
    }}
    
    /* File Uploader Area */
    [data-testid="stFileUploader"] section {{
        background-color: {THEME['surface_subtle']} !important;
        border: 1px dashed {THEME['border']} !important;
        border-radius: 6px !important;
    }}
    [data-testid="stFileUploader"] section * {{
        color: {THEME['text_primary']} !important;
    }}
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# 3. ROBUST API CLIENT & HELPERS
# ==============================================================================
def check_health():
    """Verify backend connectivity."""
    try:
        url = f"{st.session_state.backend_url}/health"
        start = time.time()
        res = requests.get(url, timeout=2.5)
        latency = int((time.time() - start) * 1000)
        if res.status_code == 200:
            return True, f"Online ({latency}ms)"
        return False, f"HTTP {res.status_code}"
    except Exception:
        return False, "Offline"


def api_call(method, endpoint, json_body=None, files=None, require_auth=True, timeout=None):
    """Unified API client with authentication and clean error messaging."""
    url = f"{st.session_state.backend_url.rstrip('/')}/{endpoint.lstrip('/')}"
    headers = {}

    if require_auth:
        token = st.session_state.token
        if not token:
            return False, {"error": "Authentication required. Please sign in."}
        headers["Authorization"] = f"Bearer {token}"

    try:
        if method.upper() == "GET":
            resp = requests.get(url, headers=headers, timeout=timeout or 15)
        elif method.upper() == "POST":
            if files:
                resp = requests.post(url, headers=headers, files=files, timeout=timeout or 300)
            else:
                headers["Content-Type"] = "application/json"
                resp = requests.post(url, headers=headers, json=json_body, timeout=timeout or 120)
        elif method.upper() == "DELETE":
            resp = requests.delete(url, headers=headers, timeout=timeout or 10)
        else:
            return False, {"error": f"Method {method} is not supported"}

        if resp.status_code in (200, 201):
            return True, resp.json()
        elif resp.status_code == 401:
            st.session_state.token = None
            st.session_state.user = None
            if "token" in st.query_params:
                del st.query_params["token"]
            return False, {"error": "Your session has expired. Please sign in again."}
        else:
            try:
                err = resp.json().get("detail", resp.text)
            except Exception:
                err = resp.text
            return False, {"error": err or f"HTTP {resp.status_code}"}

    except requests.exceptions.ConnectionError:
        return False, {"error": f"Cannot reach the backend server at {st.session_state.backend_url}. Verify the service is active."}
    except requests.exceptions.Timeout:
        return False, {"error": "The request timed out. The knowledge engine is processing your document or question."}
    except Exception as e:
        return False, {"error": str(e)}


def sync_user_profile():
    """Verify session validity and hydrate current user state."""
    if not st.session_state.token:
        return False
    ok, res = api_call("GET", "/auth/me", require_auth=True)
    if ok and isinstance(res, dict):
        st.session_state.user = res
        return True
    return False


def refresh_conversations():
    """Fetch user conversation threads."""
    if not st.session_state.token:
        return []
    ok, res = api_call("GET", "/chat/conversations", require_auth=True)
    if ok and isinstance(res, list):
        st.session_state.conversations = res
        return res
    return []


def refresh_documents():
    """Fetch user indexed documents."""
    if not st.session_state.token:
        return []
    ok, res = api_call("GET", "/documents", require_auth=True)
    if ok and isinstance(res, list):
        st.session_state.user_docs = res
        return res
    return []


def load_conversation(conv_id):
    """Load messages for a selected conversation thread."""
    ok, res = api_call("GET", f"/chat/conversations/{conv_id}", require_auth=True)
    if ok and "messages" in res:
        st.session_state.current_conversation_id = conv_id
        st.session_state.current_conversation_title = res.get("title", f"Thread #{conv_id}")
        msgs = []
        for m in res["messages"]:
            sources = []
            if m.get("sources"):
                if isinstance(m["sources"], str):
                    sources = [s.strip() for s in m["sources"].split(",") if s.strip()]
                elif isinstance(m["sources"], list):
                    sources = m["sources"]
            msgs.append({
                "role": m["role"],
                "content": m["content"],
                "sources": sources,
                "created_at": m.get("created_at")
            })
        st.session_state.messages = msgs
        return True
    return False


# ==============================================================================
# 4. AUTHENTICATION VIEW (Sign In & Registration)
# ==============================================================================
def render_auth():
    is_online, status_txt = check_health()
    badge_cls = "badge-status-online" if is_online else "badge-status-offline"

    col_l, col_center, col_r = st.columns([1, 1.8, 1])

    with col_center:
        st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

        # Institutional Header
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 1.75rem;">
            <div class="brand-mark" style="justify-content: center; font-size: 2rem; margin-bottom: 0.35rem;">
                CampusMind <span class="brand-dot"></span>
            </div>
            <p style="color: {THEME['text_secondary']}; font-size: 0.95rem; margin-bottom: 0.75rem;">
                Academic AI & Knowledge Retrieval Platform
            </p>
            <span class="academic-badge {badge_cls}">
                Backend API {status_txt}
            </span>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.auth_notice:
            st.info(st.session_state.auth_notice)
            st.session_state.auth_notice = None

        st.markdown('<div class="academic-card">', unsafe_allow_html=True)
        tab_sign_in, tab_sign_up, tab_quick = st.tabs(["Sign In", "Create Account", "Institutional Demo"])

        # --- 1. SIGN IN ---
        with tab_sign_in:
            with st.form("signin_form"):
                login_email = st.text_input("Institutional Email", placeholder="student@university.edu", key="auth_login_email")
                login_pwd = st.text_input("Password", type="password", placeholder="Enter your password", key="auth_login_pwd")
                submit_login = st.form_submit_button("Sign In", use_container_width=True)

                if submit_login:
                    if not login_email.strip() or not login_pwd.strip():
                        st.error("Please provide both your email and password.")
                    else:
                        with st.spinner("Verifying credentials..."):
                            ok, res = api_call("POST", "/auth/login", json_body={"email": login_email.strip(), "password": login_pwd}, require_auth=False)
                            if ok and "access_token" in res:
                                st.session_state.token = res["access_token"]
                                st.query_params.clear()
                                sync_user_profile()
                                if not st.session_state.user:
                                    st.session_state.user = res.get("user") or {"email": login_email, "name": login_email.split("@")[0].title()}
                                refresh_conversations()
                                refresh_documents()
                                st.session_state.page = "dashboard"
                                st.rerun()
                            else:
                                st.error(res.get("error", "Invalid institutional email or password."))

        # --- 2. REGISTER ---
        with tab_sign_up:
            with st.form("register_form"):
                reg_name = st.text_input("Full Name", placeholder="Jane Doe", key="auth_reg_name")
                reg_email = st.text_input("Institutional Email", placeholder="jane@university.edu", key="auth_reg_email")
                reg_pwd = st.text_input("Password", type="password", placeholder="Minimum 6 characters", key="auth_reg_pwd")
                submit_reg = st.form_submit_button("Create Academic Account", use_container_width=True)

                if submit_reg:
                    if not reg_name.strip() or not reg_email.strip() or not reg_pwd.strip():
                        st.error("All registration fields are required.")
                    elif len(reg_pwd) < 6:
                        st.error("Password must contain at least 6 characters.")
                    else:
                        with st.spinner("Creating account..."):
                            ok, res = api_call("POST", "/auth/register", json_body={
                                "name": reg_name.strip(),
                                "email": reg_email.strip(),
                                "password": reg_pwd
                            }, require_auth=False)
                            if ok:
                                # Auto login after successful registration
                                ok_l, res_l = api_call("POST", "/auth/login", json_body={"email": reg_email.strip(), "password": reg_pwd}, require_auth=False)
                                if ok_l and "access_token" in res_l:
                                    st.session_state.token = res_l["access_token"]
                                    st.query_params.clear()
                                    st.session_state.user = {"name": reg_name, "email": reg_email}
                                    refresh_conversations()
                                    refresh_documents()
                                    st.session_state.page = "dashboard"
                                    st.rerun()
                                else:
                                    st.success("Account created successfully. Please sign in above.")
                            else:
                                st.error(res.get("error", "Registration failed. Email address may already be in use."))

        # --- 3. DEMO ---
        with tab_quick:
            st.markdown(f"<p style='color: {THEME['text_secondary']}; font-size: 0.88rem;'>One-click access to a preconfigured demonstration workspace for evaluation.</p>", unsafe_allow_html=True)
            if st.button("Launch Evaluation Workspace", use_container_width=True):
                demo_email = "demo.student@campusmind.ai"
                demo_pwd = "DemoPassword2026!"
                demo_name = "CampusMind Student"
                with st.spinner("Connecting evaluation workspace..."):
                    ok, res = api_call("POST", "/auth/login", json_body={"email": demo_email, "password": demo_pwd}, require_auth=False)
                    if not ok:
                        api_call("POST", "/auth/register", json_body={"name": demo_name, "email": demo_email, "password": demo_pwd}, require_auth=False)
                        ok, res = api_call("POST", "/auth/login", json_body={"email": demo_email, "password": demo_pwd}, require_auth=False)

                    if ok and "access_token" in res:
                        st.session_state.token = res["access_token"]
                        st.query_params.clear()
                        st.session_state.user = {"name": demo_name, "email": demo_email}
                        refresh_conversations()
                        refresh_documents()
                        st.session_state.page = "dashboard"
                        st.rerun()
                    else:
                        st.error("Could not launch evaluation workspace. Ensure the backend server is active.")

        st.markdown('</div>', unsafe_allow_html=True)

        # Institutional Legal Footer Links
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            if st.button("Terms of Service", key="auth_btn_terms", use_container_width=True, type="secondary"):
                st.session_state.page = "terms"
                st.rerun()
        with col_f2:
            if st.button("Privacy Policy", key="auth_btn_privacy", use_container_width=True, type="secondary"):
                st.session_state.page = "privacy"
                st.rerun()


# ==============================================================================
# 5. SIDEBAR NAVIGATION
# ==============================================================================
def render_sidebar():
    with st.sidebar:
        # Brand Header
        st.markdown(f"""
        <div style="padding: 0.25rem 0 1rem 0; border-bottom: 1px solid {THEME['border']}; margin-bottom: 1.25rem;">
            <div class="brand-mark">
                CampusMind <span class="brand-dot"></span>
            </div>
            <div style="font-size: 0.74rem; color: {THEME['text_secondary']}; margin-top: 2px;">
                Academic Knowledge Platform
            </div>
        </div>
        """, unsafe_allow_html=True)

        # User Profile Capsule
        user_name = st.session_state.user.get("name", "Student") if st.session_state.user else "Student"
        user_email = st.session_state.user.get("email", "") if st.session_state.user else ""

        st.markdown(f"""
        <div class="academic-card-subtle" style="padding: 10px 12px; margin-bottom: 1.25rem;">
            <div style="font-weight: 600; font-size: 0.86rem; color: {THEME['text_primary']}; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                {user_name}
            </div>
            <div style="font-size: 0.72rem; color: {THEME['text_muted']}; font-family: 'IBM Plex Mono', monospace; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                {user_email}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Primary Navigation
        st.markdown(f"<div style='font-size: 0.7rem; font-weight: 700; color: {THEME['text_muted']}; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px;'>Workspace</div>", unsafe_allow_html=True)

        navs = [
            ("dashboard", "Academic Dashboard"),
            ("chat", "AI Research Assistant"),
            ("documents", "Document Knowledge Base"),
            ("settings", "System Settings"),
        ]

        for key, label in navs:
            is_active = (st.session_state.page == key)
            if st.button(
                label,
                key=f"nav_{key}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                st.session_state.page = key
                st.rerun()

        st.markdown(f"<div style='margin: 12px 0; border-top: 1px solid {THEME['border']};'></div>", unsafe_allow_html=True)

        # Conversation History Drawer (Shown on Chat and Dashboard)
        if st.session_state.page in ("chat", "dashboard"):
            st.markdown(f"<div style='font-size: 0.7rem; font-weight: 700; color: {THEME['text_muted']}; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px;'>Recent Threads</div>", unsafe_allow_html=True)

            if st.button("New Research Thread", key="sidebar_new_chat", use_container_width=True):
                st.session_state.current_conversation_id = None
                st.session_state.current_conversation_title = "New Research Thread"
                st.session_state.messages = []
                st.session_state.page = "chat"
                st.rerun()

            convs = st.session_state.conversations or refresh_conversations()
            if convs:
                st.markdown('<div style="max-height: 220px; overflow-y: auto; margin-top: 6px;">', unsafe_allow_html=True)
                for c in convs:
                    cid = c.get("id")
                    title = c.get("title", f"Thread #{cid}")
                    if len(title) > 28:
                        title = title[:26] + "..."
                    is_cur = (st.session_state.current_conversation_id == cid and st.session_state.page == "chat")
                    if st.button(
                        title,
                        key=f"c_btn_{cid}",
                        use_container_width=True,
                        type="primary" if is_cur else "secondary"
                    ):
                        load_conversation(cid)
                        st.session_state.page = "chat"
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.caption("No saved threads.")

            st.markdown(f"<div style='margin: 12px 0; border-top: 1px solid {THEME['border']};'></div>", unsafe_allow_html=True)

        # Legal & Institutional Links
        st.markdown(f"<div style='font-size: 0.7rem; font-weight: 700; color: {THEME['text_muted']}; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px;'>Institutional</div>", unsafe_allow_html=True)
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            if st.button("Terms", key="nav_terms", use_container_width=True, type="secondary"):
                st.session_state.page = "terms"
                st.rerun()
        with col_l2:
            if st.button("Privacy", key="nav_privacy", use_container_width=True, type="secondary"):
                st.session_state.page = "privacy"
                st.rerun()

        # Sign Out
        st.markdown(f"<div style='margin: 8px 0;'></div>", unsafe_allow_html=True)
        if st.button("Sign Out", key="btn_logout", use_container_width=True, type="secondary"):
            st.session_state.token = None
            st.session_state.user = None
            st.session_state.messages = []
            st.session_state.current_conversation_id = None
            st.query_params.clear()
            st.rerun()


# ==============================================================================
# 6. SCREEN 1: MAIN ACADEMIC DASHBOARD
# ==============================================================================
def render_dashboard():
    user_name = st.session_state.user.get("name", "Student") if st.session_state.user else "Student"
    user_docs = st.session_state.user_docs or refresh_documents()
    convs = st.session_state.conversations or refresh_conversations()
    is_online, _ = check_health()

    # Workspace Header
    st.markdown(f"""
    <div style="border-bottom: 1px solid {THEME['border']}; padding-bottom: 0.85rem; margin-bottom: 1.5rem;">
        <h2 style="font-size: 1.55rem; margin-bottom: 0.25rem;">Academic Workspace</h2>
        <div style="font-size: 0.88rem; color: {THEME['text_secondary']};">
            Welcome, {user_name}. Select an active course document, resume a research thread, or start a grounded inquiry.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Institutional Metrics Summary Strip
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.markdown(f"""
        <div class="academic-card-subtle" style="padding: 1rem 1.25rem;">
            <div style="font-size: 0.74rem; font-weight: 700; color: {THEME['text_muted']}; text-transform: uppercase;">Indexed Documents</div>
            <div style="font-family: 'Source Serif 4', Georgia, serif; font-size: 1.75rem; font-weight: 700; color: {THEME['text_primary']}; margin-top: 4px;">
                {len(user_docs)}
            </div>
            <div style="font-size: 0.74rem; color: {THEME['text_secondary']};">Available for citation grounding</div>
        </div>
        """, unsafe_allow_html=True)

    with col_m2:
        st.markdown(f"""
        <div class="academic-card-subtle" style="padding: 1rem 1.25rem;">
            <div style="font-size: 0.74rem; font-weight: 700; color: {THEME['text_muted']}; text-transform: uppercase;">Research Threads</div>
            <div style="font-family: 'Source Serif 4', Georgia, serif; font-size: 1.75rem; font-weight: 700; color: {THEME['text_primary']}; margin-top: 4px;">
                {len(convs)}
            </div>
            <div style="font-size: 0.74rem; color: {THEME['text_secondary']};">Active inquiry sessions recorded</div>
        </div>
        """, unsafe_allow_html=True)

    with col_m3:
        status_text = "Verified Online" if is_online else "Service Disconnected"
        badge_style = "badge-status-online" if is_online else "badge-status-offline"
        st.markdown(f"""
        <div class="academic-card-subtle" style="padding: 1rem 1.25rem;">
            <div style="font-size: 0.74rem; font-weight: 700; color: {THEME['text_muted']}; text-transform: uppercase;">Knowledge Engine</div>
            <div style="margin-top: 8px;">
                <span class="academic-badge {badge_style}">{status_text}</span>
            </div>
            <div style="font-size: 0.74rem; color: {THEME['text_secondary']}; margin-top: 6px;">Neural RAG & Hybrid Retrieval</div>
        </div>
        """, unsafe_allow_html=True)

    # Main Two-Column Academic Split
    col_left, col_right = st.columns([1.2, 1.8])

    with col_left:
        st.markdown('<div class="academic-card">', unsafe_allow_html=True)
        st.markdown("<h3 style='font-size: 1.15rem;'>Knowledge Base Files</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size: 0.82rem; color: {THEME['text_secondary']}; margin-bottom: 1rem;'>Documents indexed in ChromaDB for grounded RAG answers.</p>", unsafe_allow_html=True)

        if not user_docs:
            st.markdown(f"""
            <div style="padding: 1.25rem; border: 1px dashed {THEME['border']}; border-radius: 6px; text-align: center; color: {THEME['text_muted']}; font-size: 0.84rem;">
                No course documents uploaded yet. Upload syllabus or lecture notes to ground AI answers in your syllabus.
            </div>
            """, unsafe_allow_html=True)
        else:
            for d in user_docs[:5]:
                fname = d.get("filename", "Document")
                ftype = d.get("file_type", "pdf").upper()
                uploaded = str(d.get("uploaded_at", ""))[:10]
                st.markdown(f"""
                <div style="padding: 8px 0; border-bottom: 1px solid {THEME['border_subtle']}; display: flex; justify-content: space-between; align-items: center;">
                    <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 70%;">
                        <span style="font-weight: 600; font-size: 0.85rem; color: {THEME['text_primary']};">{fname}</span>
                        <div style="font-size: 0.72rem; color: {THEME['text_muted']}; font-family: 'IBM Plex Mono', monospace;">{ftype} • {uploaded}</div>
                    </div>
                    <span class="academic-badge badge-powder">Indexed</span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        if st.button("Manage Document Knowledge Base", use_container_width=True, type="secondary"):
            st.session_state.page = "documents"
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="academic-card">', unsafe_allow_html=True)
        st.markdown("<h3 style='font-size: 1.15rem;'>Recent Research Sessions</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size: 0.82rem; color: {THEME['text_secondary']}; margin-bottom: 1rem;'>Resume ongoing questions or start a new inquiry thread.</p>", unsafe_allow_html=True)

        if not convs:
            st.markdown(f"""
            <div style="padding: 1.25rem; border: 1px dashed {THEME['border']}; border-radius: 6px; text-align: center; color: {THEME['text_muted']}; font-size: 0.84rem;">
                No study threads started yet.
            </div>
            """, unsafe_allow_html=True)
        else:
            for c in convs[:5]:
                cid = c.get("id")
                title = c.get("title", f"Thread #{cid}")
                c_col1, c_col2 = st.columns([3, 1])
                with c_col1:
                    st.markdown(f"<div style='font-weight: 600; font-size: 0.88rem; padding: 6px 0;'>{title}</div>", unsafe_allow_html=True)
                with c_col2:
                    if st.button("Resume", key=f"dash_resume_{cid}", use_container_width=True, type="secondary"):
                        load_conversation(cid)
                        st.session_state.page = "chat"
                        st.rerun()

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        if st.button("Start New Inquiry Thread", use_container_width=True, type="primary"):
            st.session_state.current_conversation_id = None
            st.session_state.current_conversation_title = "New Research Thread"
            st.session_state.messages = []
            st.session_state.page = "chat"
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # Scholarly Inquiry Starters
    st.markdown('<div class="academic-card">', unsafe_allow_html=True)
    st.markdown("<h3 style='font-size: 1.15rem;'>Academic Research Starters</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size: 0.82rem; color: {THEME['text_secondary']}; margin-bottom: 0.75rem;'>Common structured inquiries grounded in academic coursework and regulations:</p>", unsafe_allow_html=True)

    q1, q2 = st.columns(2)
    with q1:
        if st.button("Examine attendance regulations and exam eligibility criteria", use_container_width=True, type="secondary"):
            st.session_state.suggested_prompt = "What are the specific attendance regulations and minimum eligibility criteria for semester examinations according to the uploaded policy documents?"
            st.session_state.page = "chat"
            st.rerun()
        if st.button("Summarize fundamental principles and definitions from lecture notes", use_container_width=True, type="secondary"):
            st.session_state.suggested_prompt = "Provide a comprehensive, structured summary of the fundamental principles and core definitions covered in the uploaded course notes."
            st.session_state.page = "chat"
            st.rerun()

    with q2:
        if st.button("Explain academic grading scale, SGPA, and CGPA formulas", use_container_width=True, type="secondary"):
            st.session_state.suggested_prompt = "Explain how the academic grading scale operates, including the specific mathematical formulas used to calculate SGPA and cumulative CGPA."
            st.session_state.page = "chat"
            st.rerun()
        if st.button("Review placement policy, eligibility cutoffs, and selection criteria", use_container_width=True, type="secondary"):
            st.session_state.suggested_prompt = "What are the eligibility cutoffs, backlogs policy, and recruitment criteria outlined in the institutional placement guidelines?"
            st.session_state.page = "chat"
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# 7. SCREEN 2: AI CHAT ASSISTANT
# ==============================================================================
def render_chat():
    title = st.session_state.current_conversation_title or "New Research Thread"

    # Header Bar
    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid {THEME['border']}; padding-bottom: 0.75rem; margin-bottom: 1.25rem;">
        <div>
            <h2 style="font-size: 1.45rem; margin: 0;">{title}</h2>
            <div style="font-size: 0.82rem; color: {THEME['text_secondary']}; margin-top: 2px;">
                Answers synthesized from uploaded course documents with direct citation citations.
            </div>
        </div>
        <div>
            <span class="academic-badge badge-powder">Neural RAG Engine Active</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Document Focus Selector
    user_docs = st.session_state.user_docs or refresh_documents()
    doc_options = {"all": "All Uploaded Knowledge Base Documents"}
    for d in user_docs:
        doc_options[str(d["id"])] = f"Document: {d['filename']}"

    col_sel, col_btn = st.columns([3.2, 1])
    with col_sel:
        selected_doc_key = st.selectbox(
            "Knowledge Base Scope:",
            options=list(doc_options.keys()),
            format_func=lambda k: doc_options.get(k, k),
            key="chat_doc_focus_selector",
            help="Target a specific syllabus or search across all indexed files."
        )
    with col_btn:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("New Thread", key="btn_header_new_chat", use_container_width=True, type="secondary"):
            st.session_state.current_conversation_id = None
            st.session_state.current_conversation_title = "New Research Thread"
            st.session_state.messages = []
            st.rerun()

    active_doc_id = int(selected_doc_key) if selected_doc_key != "all" and selected_doc_key.isdigit() else None

    # Empty State Guidance
    if not st.session_state.messages:
        user_name = st.session_state.user.get("name", "Student").split()[0] if st.session_state.user else "Student"

        st.markdown(f"""
        <div class="academic-card-subtle" style="margin-bottom: 1.5rem;">
            <h3 style="font-size: 1.2rem; margin-top: 0; margin-bottom: 0.35rem;">Academic Research Assistant</h3>
            <p style="color: {THEME['text_secondary']}; font-size: 0.88rem; margin-bottom: 0;">
                CampusMind retrieves relevant excerpts from your uploaded syllabi, lecture slides, and institutional regulations 
                to generate grounded, structured academic answers. Ask a question below to begin.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Message Stream
    for m in st.session_state.messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        sources = m.get("sources", [])

        if role == "user":
            st.markdown(f"""
            <div style="background-color: {THEME['surface_subtle']}; border: 1px solid {THEME['border']}; border-radius: 6px; padding: 1rem 1.25rem; margin-bottom: 0.9rem;">
                <div style="font-size: 0.72rem; font-weight: 700; color: {THEME['text_muted']}; text-transform: uppercase; font-family: 'IBM Plex Mono', monospace; margin-bottom: 4px;">Student</div>
                <div style="color: {THEME['text_primary']}; font-size: 0.92rem; line-height: 1.5;">{content}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background-color: {THEME['surface']}; border: 1px solid {THEME['border']}; border-radius: 6px; padding: 1.25rem 1.5rem; margin-bottom: 1rem; box-shadow: {THEME['card_shadow']};">
                <div style="font-size: 0.72rem; font-weight: 700; color: {THEME['accent']}; text-transform: uppercase; font-family: 'IBM Plex Mono', monospace; margin-bottom: 8px;">CampusMind Assistant</div>
            """, unsafe_allow_html=True)
            st.markdown(content)

            if sources:
                sources_html = "".join([f'<span class="academic-badge badge-powder">{s}</span>' for s in sources])
                st.markdown(f"""
                <div style="margin-top: 0.85rem; padding-top: 0.6rem; border-top: 1px solid {THEME['border_subtle']};">
                    <span style="font-size: 0.72rem; font-weight: 600; color: {THEME['text_muted']}; font-family: 'IBM Plex Mono', monospace; margin-right: 8px;">SOURCES:</span>
                    {sources_html}
                </div>
                """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

    # Chat Input Handling
    pending = None
    if st.session_state.suggested_prompt:
        pending = st.session_state.suggested_prompt
        st.session_state.suggested_prompt = None

    chat_input_val = st.chat_input("Inquire about your uploaded documents, syllabus, or academic policies...")
    prompt = chat_input_val or pending

    if prompt:
        # Append User Message
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "sources": [],
            "created_at": datetime.now().isoformat()
        })

        st.markdown(f"""
        <div style="background-color: {THEME['surface_subtle']}; border: 1px solid {THEME['border']}; border-radius: 6px; padding: 1rem 1.25rem; margin-bottom: 0.9rem;">
            <div style="font-size: 0.72rem; font-weight: 700; color: {THEME['text_muted']}; text-transform: uppercase; font-family: 'IBM Plex Mono', monospace; margin-bottom: 4px;">Student</div>
            <div style="color: {THEME['text_primary']}; font-size: 0.92rem; line-height: 1.5;">{prompt}</div>
        </div>
        """, unsafe_allow_html=True)

        # Assistant Generation
        with st.spinner("Retrieving document context and generating answer..."):
            payload = {"question": prompt}
            if st.session_state.current_conversation_id:
                payload["conversation_id"] = st.session_state.current_conversation_id
            if active_doc_id is not None:
                payload["document_id"] = active_doc_id

            ok, res = api_call("POST", "/chat/ask", json_body=payload, require_auth=True, timeout=120)

            if ok:
                ans = res.get("answer", "No answer generated.")
                sources = res.get("sources", [])
                cid = res.get("conversation_id")

                if cid:
                    st.session_state.current_conversation_id = cid
                    if st.session_state.current_conversation_title in ("New Chat", "New Research Thread"):
                        st.session_state.current_conversation_title = prompt[:38] + ("..." if len(prompt) > 38 else "")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": ans,
                    "sources": sources,
                    "created_at": datetime.now().isoformat()
                })

                refresh_conversations()
                st.rerun()
            else:
                st.error(f"Error: {res.get('error', 'Could not retrieve answer from knowledge engine.')}")


# ==============================================================================
# 8. SCREEN 3: DOCUMENT MANAGEMENT
# ==============================================================================
def render_documents():
    st.markdown(f"""
    <div style="border-bottom: 1px solid {THEME['border']}; padding-bottom: 0.85rem; margin-bottom: 1.5rem;">
        <h2 style="font-size: 1.55rem; margin-bottom: 0.25rem;">Document Knowledge Base</h2>
        <div style="font-size: 0.88rem; color: {THEME['text_secondary']};">
            Upload PDF or DOCX academic files. Scanned documents are parsed using optical character recognition (OCR) and vectorized into ChromaDB.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_up, col_list = st.columns([1.2, 1.8])

    # Upload Container
    with col_up:
        st.markdown('<div class="academic-card">', unsafe_allow_html=True)
        st.markdown("<h3 style='font-size: 1.15rem;'>Upload Course Material</h3>", unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Select an academic file",
            type=["pdf", "docx"],
            help="PDF textbooks, lecture slides, scanned handwritten notes, and DOCX files are supported."
        )

        if uploaded_file is not None:
            file_kb = round(uploaded_file.size / 1024, 1)
            st.markdown(f"""
            <div class="academic-card-subtle" style="padding: 10px 12px; margin: 12px 0;">
                <div style="font-weight: 600; font-size: 0.86rem;">{uploaded_file.name}</div>
                <div style="font-size: 0.72rem; color: {THEME['text_muted']}; font-family: 'IBM Plex Mono', monospace;">Size: {file_kb} KB</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Process & Index Document", use_container_width=True, type="primary"):
                with st.spinner(f"Extracting and indexing {uploaded_file.name}..."):
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    ok, res = api_call("POST", "/documents/upload", files=files, require_auth=True)

                    if ok:
                        doc_id = res.get("id")
                        filename = res.get("filename")
                        st.success(f"Successfully indexed {filename} (ID #{doc_id}) into knowledge base.")
                        refresh_documents()
                        st.rerun()
                    else:
                        st.error(f"Upload failed: {res.get('error', 'Document processing error')}")

        st.markdown('</div>', unsafe_allow_html=True)

    # Document List
    with col_list:
        st.markdown('<div class="academic-card">', unsafe_allow_html=True)
        st.markdown("<h3 style='font-size: 1.15rem;'>Indexed Course Documents</h3>", unsafe_allow_html=True)

        docs = refresh_documents()
        if not docs:
            st.markdown(f"""
            <div style="padding: 1.25rem; border: 1px dashed {THEME['border']}; border-radius: 6px; text-align: center; color: {THEME['text_muted']}; font-size: 0.84rem;">
                No files uploaded yet. Select a file on the left to index your course materials.
            </div>
            """, unsafe_allow_html=True)
        else:
            for doc in docs:
                doc_id = doc.get("id")
                fname = doc.get("filename")
                ftype = doc.get("file_type", "pdf").upper()
                uploaded_at = str(doc.get("uploaded_at", ""))[:10]

                col_d1, col_d2, col_d3 = st.columns([3.5, 1.4, 1.1])
                with col_d1:
                    st.markdown(f"<div style='font-weight: 600; font-size: 0.88rem;'>{fname}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size: 0.72rem; color: {THEME['text_muted']}; font-family: 'IBM Plex Mono', monospace;'>Format: {ftype} • Indexed: {uploaded_at}</div>", unsafe_allow_html=True)
                with col_d2:
                    st.markdown("<span class='academic-badge badge-powder'>Indexed</span>", unsafe_allow_html=True)
                with col_d3:
                    if st.button("Delete", key=f"del_doc_{doc_id}", use_container_width=True, type="secondary"):
                        ok_del, _ = api_call("DELETE", f"/documents/{doc_id}", require_auth=True)
                        if ok_del:
                            st.success("Deleted")
                            refresh_documents()
                            st.rerun()

                st.markdown(f"<div style='border-bottom: 1px solid {THEME['border_subtle']}; margin: 8px 0;'></div>", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# 9. SCREEN 4: SETTINGS & CONFIGURATION
# ==============================================================================
def render_settings():
    st.markdown(f"""
    <div style="border-bottom: 1px solid {THEME['border']}; padding-bottom: 0.85rem; margin-bottom: 1.5rem;">
        <h2 style="font-size: 1.55rem; margin-bottom: 0.25rem;">Settings & System Diagnostics</h2>
        <div style="font-size: 0.88rem; color: {THEME['text_secondary']};">
            Manage your API connection parameters, appearance mode, inspect session claims, and verify system status.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="academic-card">', unsafe_allow_html=True)
        st.markdown("<h3 style='font-size: 1.15rem;'>API Endpoint Configuration</h3>", unsafe_allow_html=True)
        new_url = st.text_input("Backend API Base URL", value=st.session_state.backend_url)

        c_b1, c_b2 = st.columns(2)
        with c_b1:
            if st.button("Save API URL", use_container_width=True, type="primary"):
                st.session_state.backend_url = new_url
                st.success("Updated API Endpoint")
                st.rerun()
        with c_b2:
            if st.button("Ping Connection", use_container_width=True, type="secondary"):
                ok, txt = check_health()
                if ok:
                    st.success(f"Status: {txt}")
                else:
                    st.error(f"Status: {txt}")

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        st.markdown("<h3 style='font-size: 1.15rem;'>Interface Appearance</h3>", unsafe_allow_html=True)

        def on_theme_change():
            val = st.session_state.get("settings_theme_radio", "")
            st.session_state.theme = "dark" if "Dark" in val else "light"

        theme_options = ["Light Mode (Default)", "Dark Mode"]
        current_idx = 0 if st.session_state.theme == "light" else 1
        st.radio(
            "Select Theme",
            theme_options,
            index=current_idx,
            key="settings_theme_radio",
            on_change=on_theme_change,
        )

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="academic-card">', unsafe_allow_html=True)
        st.markdown("<h3 style='font-size: 1.15rem;'>User Account Details</h3>", unsafe_allow_html=True)
        user = st.session_state.user or {}
        st.write(f"**Name:** {user.get('name', 'N/A')}")
        st.write(f"**Institutional Email:** {user.get('email', 'N/A')}")
        st.write(f"**Account ID:** #{user.get('id', 'N/A')}")
        st.write(f"**Authentication:** JWT Bearer Authenticated")

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        st.markdown("<h3 style='font-size: 1.15rem;'>Legal & Privacy</h3>", unsafe_allow_html=True)
        col_leg1, col_leg2 = st.columns(2)
        with col_leg1:
            if st.button("Terms of Service", key="set_terms", use_container_width=True, type="secondary"):
                st.session_state.page = "terms"
                st.rerun()
        with col_leg2:
            if st.button("Privacy Policy", key="set_privacy", use_container_width=True, type="secondary"):
                st.session_state.page = "privacy"
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("Session JWT Access Token (Developer Tool)"):
        st.code(st.session_state.token or "No active token.", language="text")
        st.caption("Use this token in Swagger UI (/docs) or API testing tools.")


# ==============================================================================
# 10. SCREEN 5: TERMS OF SERVICE
# ==============================================================================
def render_terms():
    st.markdown(f"""
    <div style="border-bottom: 1px solid {THEME['border']}; padding-bottom: 0.85rem; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h2 style="font-size: 1.55rem; margin-bottom: 0.25rem;">Terms of Service</h2>
            <div style="font-size: 0.88rem; color: {THEME['text_secondary']};">
                CampusMind Academic Platform Usage & Academic Integrity Policy
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Return to Workspace", type="primary"):
        st.session_state.page = "dashboard" if st.session_state.token else "auth"
        st.rerun()

    st.markdown('<div class="academic-card">', unsafe_allow_html=True)
    st.markdown("""
    ### 1. Purpose of the Platform
    CampusMind is an AI-powered academic assistant engineered to assist enrolled students and researchers in synthesizing, reviewing, and inquiring from their own course materials, syllabi, and lecture notes.

    ### 2. Academic Integrity & Responsible Use
    Users must uphold institutional academic honor codes. CampusMind is intended as a study aid, explanation engine, and knowledge navigation tool. It must not be utilized to facilitate academic dishonesty, unauthorized collaboration during examinations, or plagiarism.

    ### 3. Student Document Ownership
    All documents, syllabi, notes, and academic files uploaded to CampusMind remain the exclusive intellectual property of the student or respective institutional copyright holders. CampusMind claims zero ownership over your course files.

    ### 4. AI Synthesis Limitations & Verification
    CampusMind employs neural retrieval-augmented generation (RAG) to ground answers in provided documents. While designed for high precision, AI models may occasionally produce interpretations that require verification. Students are encouraged to reference the citations provided at the base of each answer.

    ### 5. Document Deletion Rights
    Students retain the unconditional right to permanently delete any uploaded document from the database and vector store at any time via the Document Knowledge Base interface.
    """)
    st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# 11. SCREEN 6: PRIVACY POLICY
# ==============================================================================
def render_privacy():
    st.markdown(f"""
    <div style="border-bottom: 1px solid {THEME['border']}; padding-bottom: 0.85rem; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h2 style="font-size: 1.55rem; margin-bottom: 0.25rem;">Privacy Policy</h2>
            <div style="font-size: 0.88rem; color: {THEME['text_secondary']};">
                Data Protection, Document Confidentiality, and Zero-Training Guarantee
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Return to Workspace", type="primary"):
        st.session_state.page = "dashboard" if st.session_state.token else "auth"
        st.rerun()

    st.markdown('<div class="academic-card">', unsafe_allow_html=True)
    st.markdown("""
    ### 1. Information Collected
    CampusMind stores:
    * **Account Information:** Name, institutional email, and securely salted bcrypt password hashes.
    * **Academic Documents:** Course files (PDF, DOCX) uploaded by the student for vector indexing.
    * **Study Threads:** Question prompts, AI responses, and citations generated within your session.

    ### 2. Zero-Model-Training Guarantee
    Your course documents, notes, exam questions, and study conversations are **never used to train public foundation models**. Document processing is executed solely in isolated retrieval pipelines for your authenticated account.

    ### 3. Document Processing & Vector Storage
    Uploaded files are processed locally via optical character recognition (OCR) and lightweight feature-hash embeddings, securely partitioned by your account ID in ChromaDB. No unauthorized student or external party has access to your indexed documents.

    ### 4. Authentication Security
    All user communications utilize industry-standard JSON Web Tokens (JWT) with HS256 signatures. Passwords are never stored in plain text.

    ### 5. Data Deletion
    When you delete a document or delete an inquiry thread, the file, its text chunks, and its vector embeddings are purged from the database immediately.
    """)
    st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# 12. MAIN CONTROLLER
# ==============================================================================
def main():
    # Hydrate user profile if token is present
    if st.session_state.token and not st.session_state.user:
        ok = sync_user_profile()
        if not ok:
            st.session_state.token = None
            if "token" in st.query_params:
                del st.query_params["token"]
        else:
            refresh_conversations()
            refresh_documents()

    # View Router
    if st.session_state.page == "terms":
        render_terms()
    elif st.session_state.page == "privacy":
        render_privacy()
    elif not st.session_state.token:
        render_auth()
    else:
        render_sidebar()
        if st.session_state.page == "dashboard":
            render_dashboard()
        elif st.session_state.page == "chat":
            render_chat()
        elif st.session_state.page == "documents":
            render_documents()
        elif st.session_state.page == "settings":
            render_settings()
        else:
            render_dashboard()


if __name__ == "__main__":
    main()
