import streamlit as st
import requests
import time
import os
from datetime import datetime

# ==============================================================================
# 1. APPLICATION & PAGE CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="CampusMind — Academic AI Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

DEFAULT_API_URL = os.environ.get("CAMPUSMIND_API_URL", "http://127.0.0.1:8000")

# Session State Setup
if "backend_url" not in st.session_state:
    st.session_state.backend_url = DEFAULT_API_URL
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "token" not in st.session_state:
    stored_token = st.query_params.get("token")
    st.session_state.token = stored_token if (stored_token and len(stored_token) > 10) else None
if "user" not in st.session_state:
    st.session_state.user = None
if "current_conversation_id" not in st.session_state:
    st.session_state.current_conversation_id = None
if "current_conversation_title" not in st.session_state:
    st.session_state.current_conversation_title = "New Chat"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversations" not in st.session_state:
    st.session_state.conversations = []
if "page" not in st.session_state:
    st.session_state.page = "chat"
if "user_docs" not in st.session_state:
    st.session_state.user_docs = []
if "suggested_prompt" not in st.session_state:
    st.session_state.suggested_prompt = None

# ==============================================================================
# 2. PROFESSIONAL DESIGN SYSTEM (Light & Dark Themes)
# ==============================================================================
is_dark = (st.session_state.theme == "dark")

if is_dark:
    THEME = {
        "bg": "#0B0F19",
        "surface": "#111827",
        "surface_card": "#162032",
        "surface_hover": "#1E293B",
        "border": "#24324D",
        "border_subtle": "rgba(255, 255, 255, 0.08)",
        "text_primary": "#F8FAFC",
        "text_secondary": "#94A3B8",
        "text_muted": "#64748B",
        "accent": "#2563EB",
        "accent_gradient": "linear-gradient(135deg, #2563EB 0%, #4F46E5 100%)",
        "accent_hover": "linear-gradient(135deg, #1D4ED8 0%, #4338CA 100%)",
        "accent_glow": "rgba(37, 99, 235, 0.25)",
        "source_badge_bg": "rgba(56, 189, 248, 0.12)",
        "source_badge_text": "#38BDF8",
        "source_badge_border": "rgba(56, 189, 248, 0.3)",
        "success": "#10B981",
        "success_bg": "rgba(16, 185, 129, 0.12)",
        "danger": "#EF4444",
        "danger_bg": "rgba(239, 68, 68, 0.12)",
        "shadow": "0 4px 20px -2px rgba(0, 0, 0, 0.35)",
    }
else:
    THEME = {
        "bg": "#F8FAFC",
        "surface": "#FFFFFF",
        "surface_card": "#FFFFFF",
        "surface_hover": "#F1F5F9",
        "border": "#E2E8F0",
        "border_subtle": "#CBD5E1",
        "text_primary": "#0F172A",
        "text_secondary": "#334155",
        "text_muted": "#64748B",
        "accent": "#2563EB",
        "accent_gradient": "linear-gradient(135deg, #2563EB 0%, #3B82F6 100%)",
        "accent_hover": "linear-gradient(135deg, #1D4ED8 0%, #2563EB 100%)",
        "accent_glow": "rgba(37, 99, 235, 0.15)",
        "source_badge_bg": "#EFF6FF",
        "source_badge_text": "#1D4ED8",
        "source_badge_border": "#BFDBFE",
        "success": "#059669",
        "success_bg": "#ECFDF5",
        "danger": "#DC2626",
        "danger_bg": "#FEF2F2",
        "shadow": "0 2px 12px -1px rgba(0, 0, 0, 0.08)",
    }

st.markdown(f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
    /* Global Reset & Typography */
    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        letter-spacing: -0.01em;
    }}
    
    .stApp {{
        background-color: {THEME['bg']} !important;
        color: {THEME['text_primary']} !important;
    }}
    
    /* General Text Elements */
    p, span, label,
    div[data-testid="stMarkdownContainer"] p, 
    [data-testid="stMarkdownContainer"] li, 
    [data-testid="stMarkdownContainer"] span {{
        color: {THEME['text_primary']} !important;
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
    
    /* Header Bar */
    header[data-testid="stHeader"] {{
        background-color: {THEME['bg']} !important;
        border-bottom: 1px solid {THEME['border']} !important;
    }}
    header[data-testid="stHeader"] * {{
        background-color: transparent !important;
    }}
    div[data-testid="stToolbar"] {{
        background-color: {THEME['bg']} !important;
    }}
    
    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: {THEME['surface']} !important;
        border-right: 1px solid {THEME['border']} !important;
    }}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p, 
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span {{
        color: {THEME['text_primary']} !important;
    }}
    
    /* Headings */
    h1, h2, h3, h4, h5, h6,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] h4 {{
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        color: {THEME['text_primary']} !important;
        letter-spacing: -0.02em !important;
    }}
    
    /* Professional Cards */
    .pro-card {{
        background-color: {THEME['surface_card']} !important;
        border: 1px solid {THEME['border']} !important;
        border-radius: 12px;
        padding: 1.5rem 1.75rem;
        box-shadow: {THEME['shadow']};
        margin-bottom: 1.25rem;
    }}
    
    /* Status Badge */
    .status-pill {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.78rem;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 9999px;
    }}
    .status-online {{
        background-color: {THEME['success_bg']};
        color: {THEME['success']} !important;
        border: 1px solid {THEME['success']};
    }}
    .status-offline {{
        background-color: {THEME['danger_bg']};
        color: {THEME['danger']} !important;
        border: 1px solid {THEME['danger']};
    }}
    .pulse-dot {{
        width: 7px;
        height: 7px;
        border-radius: 50%;
    }}
    .dot-green {{
        background-color: {THEME['success']};
        box-shadow: 0 0 6px {THEME['success']};
    }}
    .dot-red {{
        background-color: {THEME['danger']};
    }}
    
    /* Sources Badge */
    .source-pill {{
        display: inline-flex;
        align-items: center;
        gap: 5px;
        background-color: {THEME['source_badge_bg']};
        color: {THEME['source_badge_text']} !important;
        border: 1px solid {THEME['source_badge_border']};
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 500;
        margin-right: 6px;
        margin-top: 4px;
    }}
    
    /* =========================================================================
       BUTTON STYLES (EXPLICIT PRIMARY & SECONDARY CONTRAST)
       ========================================================================= */
    /* Primary Buttons (Default or kind="primary") */
    .stButton > button,
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="baseButton-primary"],
    div[data-testid="stFormSubmitButton"] > button {{
        background: {THEME['accent_gradient']} !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        padding: 0.5rem 1rem !important;
        box-shadow: 0 2px 8px {THEME['accent_glow']} !important;
        white-space: nowrap !important;
        min-height: 40px !important;
    }}
    
    .stButton > button:not([kind="secondary"]):not([data-testid="baseButton-secondary"]) *,
    .stButton > button[kind="primary"] *,
    .stButton > button[data-testid="baseButton-primary"] *,
    div[data-testid="stFormSubmitButton"] > button * {{
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 600 !important;
        white-space: nowrap !important;
    }}
    
    .stButton > button:hover {{
        opacity: 0.92 !important;
        transform: translateY(-1px);
    }}
    
    /* Secondary Buttons */
    .stButton > button[kind="secondary"],
    .stButton > button[data-testid="baseButton-secondary"] {{
        background: {THEME['surface_card']} !important;
        background-color: {THEME['surface_card']} !important;
        background-image: none !important;
        color: {THEME['text_primary']} !important;
        -webkit-text-fill-color: {THEME['text_primary']} !important;
        border: 1px solid {THEME['border']} !important;
        box-shadow: none !important;
        font-weight: 500 !important;
        white-space: nowrap !important;
    }}
    
    .stButton > button[kind="secondary"] *,
    .stButton > button[kind="secondary"] p,
    .stButton > button[kind="secondary"] span,
    .stButton > button[kind="secondary"] div,
    .stButton > button[data-testid="baseButton-secondary"] *,
    .stButton > button[data-testid="baseButton-secondary"] p,
    .stButton > button[data-testid="baseButton-secondary"] span,
    .stButton > button[data-testid="baseButton-secondary"] div {{
        color: {THEME['text_primary']} !important;
        -webkit-text-fill-color: {THEME['text_primary']} !important;
        font-weight: 500 !important;
        white-space: nowrap !important;
    }}
    
    .stButton > button[kind="secondary"]:hover,
    .stButton > button[data-testid="baseButton-secondary"]:hover {{
        background-color: {THEME['surface_hover']} !important;
        border-color: {THEME['accent']} !important;
    }}
    .stButton > button[kind="secondary"]:hover *,
    .stButton > button[data-testid="baseButton-secondary"]:hover * {{
        color: {THEME['accent']} !important;
        -webkit-text-fill-color: {THEME['accent']} !important;
    }}
    
    /* =========================================================================
       FORM INPUTS & SELECTBOXES (UNIFIED BACKGROUND & TEXT)
       ========================================================================= */
    .stTextInput > div,
    .stTextInput > div > div,
    div[data-baseweb="input"],
    div[data-baseweb="input"] > div,
    div[data-baseweb="base-input"],
    .stSelectbox > div,
    .stSelectbox > div > div,
    div[data-baseweb="select"],
    div[data-baseweb="select"] > div {{
        background-color: {THEME['surface_card']} !important;
        color: {THEME['text_primary']} !important;
        -webkit-text-fill-color: {THEME['text_primary']} !important;
        border: 1px solid {THEME['border']} !important;
        border-radius: 8px !important;
    }}
    
    .stTextInput input,
    .stSelectbox input {{
        background-color: transparent !important;
        color: {THEME['text_primary']} !important;
        -webkit-text-fill-color: {THEME['text_primary']} !important;
        border: none !important;
        font-size: 0.9rem !important;
        padding: 0.5rem 0.75rem !important;
    }}
    
    .stTextInput input::placeholder {{
        color: {THEME['text_muted']} !important;
        -webkit-text-fill-color: {THEME['text_muted']} !important;
    }}
    
    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="select"]:focus-within {{
        border-color: {THEME['accent']} !important;
        box-shadow: 0 0 0 2px {THEME['accent_glow']} !important;
    }}
    
    /* BaseWeb Dropdown Popovers */
    div[data-baseweb="popover"],
    div[data-baseweb="menu"],
    ul[data-baseweb="menu"],
    li[role="option"] {{
        background-color: {THEME['surface_card']} !important;
        color: {THEME['text_primary']} !important;
    }}
    li[role="option"]:hover,
    li[role="option"][aria-selected="true"] {{
        background-color: {THEME['surface_hover']} !important;
        color: {THEME['accent']} !important;
    }}
    li[role="option"] * {{
        color: {THEME['text_primary']} !important;
    }}
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {{
        border-bottom: 1px solid {THEME['border']};
        gap: 8px;
    }}
    .stTabs [data-baseweb="tab"] {{
        color: {THEME['text_secondary']} !important;
        border-radius: 6px;
        padding: 6px 14px;
        font-size: 0.88rem;
        font-weight: 500;
        background-color: transparent !important;
    }}
    .stTabs [data-baseweb="tab"] * {{
        color: {THEME['text_secondary']} !important;
    }}
    .stTabs [aria-selected="true"] {{
        color: {THEME['accent']} !important;
        font-weight: 600 !important;
        border-bottom: 2px solid {THEME['accent']} !important;
    }}
    .stTabs [aria-selected="true"] * {{
        color: {THEME['accent']} !important;
    }}
    
    /* Chat Messages */
    [data-testid="stChatMessage"] {{
        background-color: {THEME['surface_card']} !important;
        border: 1px solid {THEME['border']} !important;
        border-radius: 10px !important;
        padding: 1rem 1.25rem !important;
        margin-bottom: 0.85rem !important;
        box-shadow: {THEME['shadow']};
    }}
    [data-testid="stChatMessage"] p, 
    [data-testid="stChatMessage"] span, 
    [data-testid="stChatMessage"] li, 
    [data-testid="stChatMessage"] div {{
        color: {THEME['text_primary']} !important;
    }}
    
    /* Markdown Tables */
    table {{
        background-color: {THEME['surface_card']} !important;
        color: {THEME['text_primary']} !important;
        border-collapse: collapse !important;
        border: 1px solid {THEME['border']} !important;
        width: 100% !important;
        margin: 12px 0 !important;
        border-radius: 6px !important;
        overflow: hidden !important;
    }}
    th {{
        background-color: {THEME['surface_hover']} !important;
        color: {THEME['text_primary']} !important;
        font-weight: 600 !important;
        border: 1px solid {THEME['border']} !important;
        padding: 8px 12px !important;
        text-align: left !important;
    }}
    td {{
        color: {THEME['text_primary']} !important;
        border: 1px solid {THEME['border']} !important;
        padding: 8px 12px !important;
    }}
    
    /* Code Blocks & Inline Code */
    code:not(.source-pill) {{
        background-color: {THEME['surface_hover']} !important;
        color: {THEME['accent']} !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85em !important;
    }}
    pre {{
        background-color: {THEME['surface_hover']} !important;
        border: 1px solid {THEME['border']} !important;
        border-radius: 8px !important;
        padding: 12px !important;
    }}
    pre code {{
        color: {THEME['text_primary']} !important;
        background-color: transparent !important;
    }}
    
    /* Chat Input */
    [data-testid="stChatInput"] {{
        background-color: {THEME['bg']} !important;
        border-top: 1px solid {THEME['border']} !important;
    }}
    [data-testid="stChatInput"] > div {{
        background-color: {THEME['surface_card']} !important;
        border: 1px solid {THEME['border']} !important;
        border-radius: 10px !important;
    }}
    [data-testid="stChatInput"] textarea {{
        color: {THEME['text_primary']} !important;
        -webkit-text-fill-color: {THEME['text_primary']} !important;
    }}
    [data-testid="stChatInput"] textarea::placeholder {{
        color: {THEME['text_muted']} !important;
        -webkit-text-fill-color: {THEME['text_muted']} !important;
    }}
    [data-testid="stChatInput"] button svg {{
        fill: {THEME['accent']} !important;
        stroke: {THEME['accent']} !important;
    }}
    
    /* File Uploader */
    [data-testid="stFileUploader"] section {{
        background-color: {THEME['surface_card']} !important;
        border: 2px dashed {THEME['border']} !important;
        border-radius: 8px !important;
    }}
    [data-testid="stFileUploader"] section * {{
        color: {THEME['text_primary']} !important;
    }}
    
    /* Alerts & Expanders */
    .stAlert {{
        background-color: {THEME['surface_card']} !important;
        border: 1px solid {THEME['border']} !important;
        color: {THEME['text_primary']} !important;
    }}
    .stAlert * {{
        color: {THEME['text_primary']} !important;
    }}
    [data-testid="stExpander"] {{
        background-color: {THEME['surface_card']} !important;
        border: 1px solid {THEME['border']} !important;
        border-radius: 8px !important;
    }}
    [data-testid="stExpander"] summary {{
        color: {THEME['text_primary']} !important;
    }}
    [data-testid="stExpander"] summary * {{
        color: {THEME['text_primary']} !important;
    }}
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# 3. ROBUST API CLIENT & HELPERS
# ==============================================================================
def check_health():
    """Verify backend connection."""
    try:
        url = f"{st.session_state.backend_url}/health"
        start = time.time()
        res = requests.get(url, timeout=2.0)
        latency = int((time.time() - start) * 1000)
        if res.status_code == 200:
            return True, f"Online ({latency}ms)"
        return False, f"Status {res.status_code}"
    except Exception:
        return False, "Offline"


def api_call(method, endpoint, json_body=None, files=None, require_auth=True):
    """Unified API client with authentication and error handling."""
    url = f"{st.session_state.backend_url.rstrip('/')}/{endpoint.lstrip('/')}"
    headers = {}
    
    if require_auth:
        token = st.session_state.token
        if not token:
            return False, {"error": "Authentication required. Please log in."}
        headers["Authorization"] = f"Bearer {token}"
        
    try:
        if method.upper() == "GET":
            resp = requests.get(url, headers=headers, timeout=15)
        elif method.upper() == "POST":
            if files:
                resp = requests.post(url, headers=headers, files=files, timeout=300)
            else:
                headers["Content-Type"] = "application/json"
                resp = requests.post(url, headers=headers, json=json_body, timeout=40)
        elif method.upper() == "DELETE":
            resp = requests.delete(url, headers=headers, timeout=10)
        else:
            return False, {"error": f"Method {method} not supported"}
            
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
            return False, {"error": err or f"Error {resp.status_code}"}
            
    except requests.exceptions.ConnectionError:
        return False, {"error": f"Could not reach backend at {st.session_state.backend_url}. Please ensure server is running."}
    except requests.exceptions.Timeout:
        return False, {"error": "Request timed out. Server is busy."}
    except Exception as e:
        return False, {"error": str(e)}


def sync_user_profile():
    """Fetch profile of current user to ensure session validity."""
    if not st.session_state.token:
        return False
    ok, res = api_call("GET", "/auth/me", require_auth=True)
    if ok and isinstance(res, dict):
        st.session_state.user = res
        return True
    return False


def refresh_conversations():
    """Fetch user's conversation threads."""
    if not st.session_state.token:
        return []
    ok, res = api_call("GET", "/chat/conversations", require_auth=True)
    if ok and isinstance(res, list):
        st.session_state.conversations = res
        return res
    return []


def refresh_documents():
    """Fetch user's uploaded documents."""
    if not st.session_state.token:
        return []
    ok, res = api_call("GET", "/documents", require_auth=True)
    if ok and isinstance(res, list):
        st.session_state.user_docs = res
        return res
    return []


def load_conversation(conv_id):
    """Load messages for a selected conversation."""
    ok, res = api_call("GET", f"/chat/conversations/{conv_id}", require_auth=True)
    if ok and "messages" in res:
        st.session_state.current_conversation_id = conv_id
        st.session_state.current_conversation_title = res.get("title", f"Chat #{conv_id}")
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
    badge_cls = "status-online" if is_online else "status-offline"
    dot_cls = "dot-green" if is_online else "dot-red"

    col_l, col_center, col_r = st.columns([1, 1.8, 1])

    with col_center:
        st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
        
        # Header Branding
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 1.5rem;">
            <div style="font-size: 42px; margin-bottom: 8px;">🎓</div>
            <h1 style="font-size: 1.85rem; margin-bottom: 0.35rem; font-weight: 700;">
                CampusMind
            </h1>
            <p style="color: {THEME['text_secondary']}; font-size: 0.95rem; margin-bottom: 0.75rem;">
                Enterprise Academic AI & Knowledge Retrieval Platform
            </p>
            <div class="status-pill {badge_cls}">
                <span class="pulse-dot {dot_cls}"></span>
                API {status_txt}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Theme Switcher Bar for Auth Page
        col_t1, col_t2 = st.columns([2, 1])
        with col_t2:
            t_label = "☀️ Light Theme" if is_dark else "🌙 Dark Theme"
            if st.button(t_label, key="auth_theme_btn", use_container_width=True, type="secondary"):
                st.session_state.theme = "light" if is_dark else "dark"
                if "settings_theme_radio" in st.session_state:
                    st.session_state.settings_theme_radio = "☀️ Light Mode" if st.session_state.theme == "light" else "🌙 Dark Mode (Default)"
                st.rerun()

        st.markdown('<div class="pro-card">', unsafe_allow_html=True)
        tab_sign_in, tab_sign_up, tab_quick = st.tabs(["Sign In", "Create Account", "⚡ Quick Demo"])
        
        # --- 1. SIGN IN TAB ---
        with tab_sign_in:
            with st.form("signin_form"):
                login_email = st.text_input("Institutional Email", placeholder="user@campus.edu", key="auth_login_email")
                login_pwd = st.text_input("Password", type="password", placeholder="••••••••", key="auth_login_pwd")
                submit_login = st.form_submit_button("Sign In →", use_container_width=True)
                
                if submit_login:
                    if not login_email.strip() or not login_pwd.strip():
                        st.error("Please enter both email and password.")
                    else:
                        with st.spinner("Authenticating credentials..."):
                            ok, res = api_call("POST", "/auth/login", json_body={"email": login_email.strip(), "password": login_pwd}, require_auth=False)
                            if ok and "access_token" in res:
                                st.session_state.token = res["access_token"]
                                st.query_params["token"] = res["access_token"]
                                sync_user_profile()
                                if not st.session_state.user:
                                    st.session_state.user = res.get("user") or {"email": login_email, "name": login_email.split("@")[0].title()}
                                refresh_conversations()
                                refresh_documents()
                                st.success("Authentication successful.")
                                time.sleep(0.3)
                                st.rerun()
                            else:
                                st.error(res.get("error", "Invalid email or password."))

        # --- 2. REGISTER TAB ---
        with tab_sign_up:
            with st.form("register_form"):
                reg_name = st.text_input("Full Name", placeholder="Jane Doe", key="auth_reg_name")
                reg_email = st.text_input("Email Address", placeholder="jane@campus.edu", key="auth_reg_email")
                reg_pwd = st.text_input("Password", type="password", placeholder="Minimum 6 characters", key="auth_reg_pwd")
                submit_reg = st.form_submit_button("Create Account ✨", use_container_width=True)
                
                if submit_reg:
                    if not reg_name.strip() or not reg_email.strip() or not reg_pwd.strip():
                        st.error("All fields are required.")
                    elif len(reg_pwd) < 6:
                        st.error("Password must be at least 6 characters.")
                    else:
                        with st.spinner("Creating account..."):
                            ok, res = api_call("POST", "/auth/register", json_body={
                                "name": reg_name.strip(),
                                "email": reg_email.strip(),
                                "password": reg_pwd
                            }, require_auth=False)
                            if ok:
                                # Auto login
                                ok_l, res_l = api_call("POST", "/auth/login", json_body={"email": reg_email.strip(), "password": reg_pwd}, require_auth=False)
                                if ok_l and "access_token" in res_l:
                                    st.session_state.token = res_l["access_token"]
                                    st.query_params["token"] = res_l["access_token"]
                                    st.session_state.user = {"name": reg_name, "email": reg_email}
                                    refresh_conversations()
                                    refresh_documents()
                                    st.success(f"Welcome, {reg_name}!")
                                    time.sleep(0.3)
                                    st.rerun()
                                else:
                                    st.success("Account created successfully. Please sign in.")
                            else:
                                st.error(res.get("error", "Registration failed. Email may already be in use."))

        # --- 3. QUICK DEMO TAB ---
        with tab_quick:
            st.markdown(f"<p style='color: {THEME['text_secondary']}; font-size: 0.85rem;'>One-click access to a preconfigured student workspace.</p>", unsafe_allow_html=True)
            if st.button("⚡ Launch Demo Student Workspace", use_container_width=True):
                demo_email = "demo.student@campusmind.ai"
                demo_pwd = "DemoPassword2026!"
                demo_name = "CampusMind Student"
                with st.spinner("Connecting demo profile..."):
                    ok, res = api_call("POST", "/auth/login", json_body={"email": demo_email, "password": demo_pwd}, require_auth=False)
                    if not ok:
                        # Auto-register demo account
                        api_call("POST", "/auth/register", json_body={"name": demo_name, "email": demo_email, "password": demo_pwd}, require_auth=False)
                        ok, res = api_call("POST", "/auth/login", json_body={"email": demo_email, "password": demo_pwd}, require_auth=False)
                    
                    if ok and "access_token" in res:
                        st.session_state.token = res["access_token"]
                        st.query_params["token"] = res["access_token"]
                        st.session_state.user = {"name": demo_name, "email": demo_email}
                        refresh_conversations()
                        refresh_documents()
                        st.rerun()
                    else:
                        st.error("Could not start demo. Please ensure backend is running.")

        st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# 5. SIDEBAR NAVIGATION & CONVERSATION DRAWER
# ==============================================================================
def render_sidebar():
    with st.sidebar:
        # App Title
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 1.25rem;">
            <div style="font-size: 24px;">🎓</div>
            <div>
                <div style="font-weight: 700; font-size: 1.15rem; color: {THEME['text_primary']};">CampusMind</div>
                <div style="font-size: 0.72rem; color: {THEME['text_muted']}; font-weight: 500;">AI Knowledge Platform</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # User Pill
        user_name = st.session_state.user.get("name", "Student") if st.session_state.user else "Student"
        user_email = st.session_state.user.get("email", "") if st.session_state.user else ""
        
        st.markdown(f"""
        <div style="background-color: {THEME['surface_card']}; border: 1px solid {THEME['border']}; border-radius: 8px; padding: 8px 12px; margin-bottom: 1.25rem; display: flex; align-items: center; gap: 10px;">
            <div style="background: {THEME['accent_gradient']}; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #FFF; font-weight: 600; font-size: 0.85rem;">
                {user_name[0].upper() if user_name else 'U'}
            </div>
            <div style="overflow: hidden; flex: 1;">
                <div style="font-weight: 600; font-size: 0.84rem; color: {THEME['text_primary']}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                    {user_name}
                </div>
                <div style="font-size: 0.72rem; color: {THEME['text_muted']}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                    {user_email}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation
        st.markdown(f"<div style='font-size: 0.72rem; font-weight: 700; color: {THEME['text_muted']}; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;'>NAVIGATION</div>", unsafe_allow_html=True)
        
        navs = [
            ("chat", "💬 Chat & Assistant"),
            ("documents", "📄 Documents & Files"),
            ("settings", "⚙️ Settings & API"),
        ]
        
        for key, label in navs:
            is_active = (st.session_state.page == key)
            if st.button(label, key=f"nav_{key}", use_container_width=True, type="primary" if is_active else "secondary"):
                st.session_state.page = key
                st.rerun()
                
        st.divider()
        
        # Conversation History (Chat Page Only)
        if st.session_state.page == "chat":
            st.markdown(f"<div style='font-size: 0.72rem; font-weight: 700; color: {THEME['text_muted']}; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;'>CHATS</div>", unsafe_allow_html=True)
            
            if st.button("➕ Start New Chat", key="sidebar_new_chat", use_container_width=True):
                st.session_state.current_conversation_id = None
                st.session_state.current_conversation_title = "New Chat"
                st.session_state.messages = []
                st.rerun()
                
            convs = st.session_state.conversations or refresh_conversations()
            if convs:
                st.markdown('<div style="max-height: 240px; overflow-y: auto; margin-top: 6px;">', unsafe_allow_html=True)
                for c in convs:
                    cid = c.get("id")
                    title = c.get("title", f"Chat #{cid}")
                    if len(title) > 26:
                        title = title[:24] + "..."
                    is_cur = (st.session_state.current_conversation_id == cid)
                    if st.button(
                        f"💬 {title}",
                        key=f"c_btn_{cid}",
                        use_container_width=True,
                        type="primary" if is_cur else "secondary"
                    ):
                        load_conversation(cid)
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.caption("No chat history yet.")
                
            st.divider()

        # Theme & Logout Footer
        col_th, col_lo = st.columns(2)
        with col_th:
            t_label = "☀️ Light" if is_dark else "🌙 Dark"
            if st.button(t_label, key="sidebar_theme_toggle_btn", use_container_width=True, type="secondary"):
                st.session_state.theme = "light" if is_dark else "dark"
                if "settings_theme_radio" in st.session_state:
                    st.session_state.settings_theme_radio = "☀️ Light Mode" if st.session_state.theme == "light" else "🌙 Dark Mode (Default)"
                st.rerun()
        with col_lo:
            if st.button("Sign Out", key="btn_logout", use_container_width=True, type="secondary"):
                st.session_state.token = None
                st.session_state.user = None
                st.session_state.messages = []
                st.session_state.current_conversation_id = None
                st.query_params.clear()
                st.rerun()


# ==============================================================================
# 6. PAGE 1: CHAT & RAG ASSISTANT
# ==============================================================================
def render_chat():
    title = st.session_state.current_conversation_title or "New Chat"
    
    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid {THEME['border']}; padding-bottom: 0.6rem; margin-bottom: 1.25rem;">
        <div>
            <h2 style="margin: 0; font-size: 1.35rem;">{title}</h2>
            <div style="font-size: 0.8rem; color: {THEME['text_secondary']}; margin-top: 2px;">
                Answers grounded in uploaded academic documents with verified citations.
            </div>
        </div>
        <div>
            <span class="source-pill">⚡ Neural RAG + OCR Active</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Document Focus Selector Bar
    user_docs = st.session_state.user_docs or refresh_documents()
    doc_options = {"all": "📚 All Uploaded Documents"}
    for d in user_docs:
        doc_options[str(d["id"])] = f"📄 {d['filename']}"

    col_sel, col_btn = st.columns([3, 1])
    with col_sel:
        selected_doc_key = st.selectbox(
            "Focus Knowledge Base (Optional):",
            options=list(doc_options.keys()),
            format_func=lambda k: doc_options.get(k, k),
            key="chat_doc_focus_selector",
            help="Target a specific document (e.g. Python Notes) or search across all your uploaded files."
        )
    with col_btn:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("➕ New Chat", key="btn_header_new_chat", use_container_width=True, type="secondary"):
            st.session_state.current_conversation_id = None
            st.session_state.current_conversation_title = "New Chat"
            st.session_state.messages = []
            st.rerun()

    active_doc_id = int(selected_doc_key) if selected_doc_key != "all" and selected_doc_key.isdigit() else None

    # Empty State: Hero Banner & Suggestion Chips
    if not st.session_state.messages:
        user_name = st.session_state.user.get("name", "Student").split()[0] if st.session_state.user else "Student"
        
        st.markdown(f"""
        <div class="pro-card" style="border-left: 4px solid {THEME['accent']}; margin-bottom: 1.5rem;">
            <h3 style="margin-top: 0; font-size: 1.25rem; margin-bottom: 0.35rem;">Welcome, {user_name}! 👋</h3>
            <p style="color: {THEME['text_secondary']}; font-size: 0.9rem; margin-bottom: 0; line-height: 1.5;">
                Ask questions from your uploaded lecture notes, regulations, syllabus, or placement policies. 
                CampusMind will search your documents and provide precise answers with source references.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"<div style='font-size: 0.82rem; font-weight: 600; color: {THEME['text_secondary']}; margin-bottom: 0.6rem;'>SUGGESTED QUERIES</div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        suggestions = [
            ("🐍 Python Operators", "What are operators in Python and what types exist?"),
            ("📦 Python Modules", "What is a module in Python and how do you import it?"),
            ("📌 Attendance Policy", "What is the minimum attendance required for semester exams?"),
            ("💼 Placement Rules", "What are the eligibility criteria and cutoff CGPA for placements?"),
        ]
        
        for i, (label, query_text) in enumerate(suggestions):
            target = col1 if i % 2 == 0 else col2
            with target:
                if st.button(f"**{label}**\n\n_{query_text}_", key=f"sug_{i}", use_container_width=True, type="secondary"):
                    st.session_state.suggested_prompt = query_text
                    st.rerun()

    # Message Stream
    for m in st.session_state.messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        sources = m.get("sources", [])
        
        with st.chat_message(role, avatar="👤" if role == "user" else "🎓"):
            st.markdown(content)
            if role == "assistant" and sources:
                sources_html = "".join([f'<span class="source-pill">📄 {s}</span>' for s in sources])
                st.markdown(f"""
                <div style="margin-top: 0.6rem; padding-top: 0.4rem; border-top: 1px solid {THEME['border_subtle']};">
                    <span style="font-size: 0.72rem; font-weight: 600; color: {THEME['text_muted']}; margin-right: 6px;">SOURCES:</span>
                    {sources_html}
                </div>
                """, unsafe_allow_html=True)

    # Input Handling
    pending = None
    if st.session_state.suggested_prompt:
        pending = st.session_state.suggested_prompt
        st.session_state.suggested_prompt = None

    chat_input_val = st.chat_input("Ask a question about your documents, syllabus, rules...")
    prompt = chat_input_val or pending

    if prompt:
        # Append User Message
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "sources": [],
            "created_at": datetime.now().isoformat()
        })
        
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # Assistant Response
        with st.chat_message("assistant", avatar="🎓"):
            with st.spinner("Retrieving document context & generating response..."):
                payload = {"question": prompt}
                if st.session_state.current_conversation_id:
                    payload["conversation_id"] = st.session_state.current_conversation_id
                if active_doc_id is not None:
                    payload["document_id"] = active_doc_id

                ok, res = api_call("POST", "/chat/ask", json_body=payload, require_auth=True)

                if ok:
                    ans = res.get("answer", "No answer generated.")
                    sources = res.get("sources", [])
                    cid = res.get("conversation_id")

                    if cid:
                        st.session_state.current_conversation_id = cid
                        if st.session_state.current_conversation_title == "New Chat":
                            st.session_state.current_conversation_title = prompt[:35] + ("..." if len(prompt) > 35 else "")

                    st.markdown(ans)

                    if sources:
                        sources_html = "".join([f'<span class="source-pill">📄 {s}</span>' for s in sources])
                        st.markdown(f"""
                        <div style="margin-top: 0.6rem; padding-top: 0.4rem; border-top: 1px solid {THEME['border_subtle']};">
                            <span style="font-size: 0.72rem; font-weight: 600; color: {THEME['text_muted']}; margin-right: 6px;">SOURCES:</span>
                            {sources_html}
                        </div>
                        """, unsafe_allow_html=True)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": ans,
                        "sources": sources,
                        "created_at": datetime.now().isoformat()
                    })

                    refresh_conversations()
                else:
                    st.error(f"Error: {res.get('error', 'Could not retrieve answer.')}")


# ==============================================================================
# 7. PAGE 2: ACCURATE DOCUMENT MANAGEMENT & UPLOADER
# ==============================================================================
def render_documents():
    st.markdown(f"""
    <div style="border-bottom: 1px solid {THEME['border']}; padding-bottom: 0.6rem; margin-bottom: 1.25rem;">
        <h2 style="margin: 0; font-size: 1.35rem;">📄 Document Knowledge Base</h2>
        <div style="font-size: 0.8rem; color: {THEME['text_secondary']}; margin-top: 2px;">
            Upload PDF or DOCX files. Scanned pages are automatically processed via optical character recognition (OCR) and indexed into ChromaDB.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col_up, col_list = st.columns([1.2, 1.8])
    
    # --- UPLOAD SECTION ---
    with col_up:
        st.markdown('<div class="pro-card">', unsafe_allow_html=True)
        st.markdown("<h3 style='font-size: 1.05rem; margin-top: 0;'>📤 Upload Document</h3>", unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Choose a PDF or DOCX file",
            type=["pdf", "docx"],
            help="Digital PDFs, Scanned handwritten PDFs, and Word documents are supported."
        )
        
        if uploaded_file is not None:
            file_kb = round(uploaded_file.size / 1024, 1)
            st.info(f"Selected: **{uploaded_file.name}** ({file_kb} KB)")
            
            if st.button("🚀 Process & Ingest File", use_container_width=True):
                with st.spinner(f"⚡ Processing and indexing {uploaded_file.name}..."):
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    ok, res = api_call("POST", "/documents/upload", files=files, require_auth=True)
                    
                    if ok:
                        doc_id = res.get("id")
                        filename = res.get("filename")
                        st.success(f"✅ Successfully indexed **{filename}** (ID #{doc_id}) into knowledge base!")
                        refresh_documents()
                        st.rerun()
                    else:
                        st.error(f"❌ Upload failed: {res.get('error', 'Internal processing error')}")
                        
        st.markdown('</div>', unsafe_allow_html=True)

    # --- DOCUMENT LIST SECTION ---
    with col_list:
        st.markdown('<div class="pro-card">', unsafe_allow_html=True)
        st.markdown("<h3 style='font-size: 1.05rem; margin-top: 0;'>📚 Indexed Knowledge Base Files</h3>", unsafe_allow_html=True)
        
        docs = refresh_documents()
        if not docs:
            st.caption("No files uploaded yet. Upload your syllabus or notes on the left.")
        else:
            for doc in docs:
                doc_id = doc.get("id")
                fname = doc.get("filename")
                ftype = doc.get("file_type", "pdf").upper()
                uploaded_at = str(doc.get("uploaded_at", ""))[:10]
                
                col_d1, col_d2, col_d3 = st.columns([3.5, 1.5, 1])
                with col_d1:
                    icon = "📕" if ftype.lower() == "pdf" else "📘"
                    st.markdown(f"**{icon} {fname}**")
                    st.caption(f"Type: `{ftype}` • Date: {uploaded_at}")
                with col_d2:
                    st.markdown("<span class='status-pill status-online'>Indexed</span>", unsafe_allow_html=True)
                with col_d3:
                    if st.button("Delete", key=f"del_doc_{doc_id}", help="Remove from database", type="secondary"):
                        ok_del, _ = api_call("DELETE", f"/documents/{doc_id}", require_auth=True)
                        if ok_del:
                            st.success("Deleted")
                            refresh_documents()
                            st.rerun()
                st.markdown(f"<div style='border-bottom: 1px solid {THEME['border']}; margin: 8px 0;'></div>", unsafe_allow_html=True)
                
        st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# 8. PAGE 3: SETTINGS & CONFIGURATION
# ==============================================================================
def render_settings():
    st.markdown(f"""
    <div style="border-bottom: 1px solid {THEME['border']}; padding-bottom: 0.6rem; margin-bottom: 1.25rem;">
        <h2 style="margin: 0; font-size: 1.35rem;">⚙️ Settings & Configuration</h2>
        <div style="font-size: 0.8rem; color: {THEME['text_secondary']}; margin-top: 2px;">
            Configure API endpoints, theme appearance, inspect user session tokens, and verify backend connectivity.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="pro-card">', unsafe_allow_html=True)
        st.markdown("<h3 style='font-size: 1.05rem; margin-top: 0;'>🌐 API Endpoint</h3>", unsafe_allow_html=True)
        new_url = st.text_input("Backend Base URL", value=st.session_state.backend_url)
        
        c_b1, c_b2 = st.columns(2)
        with c_b1:
            if st.button("Save URL", use_container_width=True):
                st.session_state.backend_url = new_url
                st.success("Updated API URL")
                st.rerun()
        with c_b2:
            if st.button("Ping Server", use_container_width=True, type="secondary"):
                ok, txt = check_health()
                if ok:
                    st.success(f"Status: {txt}")
                else:
                    st.error(f"Status: {txt}")
                    
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        st.markdown("<h3 style='font-size: 1.05rem; margin-top: 0;'>🎨 Theme Preference</h3>", unsafe_allow_html=True)
        
        def on_settings_theme_change():
            val = st.session_state.get("settings_theme_radio", "")
            st.session_state.theme = "dark" if "Dark" in val else "light"
            
        theme_options = ["🌙 Dark Mode (Default)", "☀️ Light Mode"]
        current_theme_idx = 0 if st.session_state.theme == "dark" else 1
        st.radio(
            "Select Interface Theme",
            theme_options,
            index=current_theme_idx,
            key="settings_theme_radio",
            on_change=on_settings_theme_change,
        )
            
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="pro-card">', unsafe_allow_html=True)
        st.markdown("<h3 style='font-size: 1.05rem; margin-top: 0;'>👤 User Profile</h3>", unsafe_allow_html=True)
        user = st.session_state.user or {}
        st.write(f"**Name:** {user.get('name', 'N/A')}")
        st.write(f"**Email:** {user.get('email', 'N/A')}")
        st.write(f"**User ID:** #{user.get('id', 'N/A')}")
        st.write(f"**Session:** JWT Bearer Authenticated")
        st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("🔑 Session JWT Access Token (Developer Tool)"):
        st.code(st.session_state.token or "No active token.", language="text")
        st.caption("Use this token in Swagger UI (/docs) or API requests.")


# ==============================================================================
# 9. MAIN CONTROLLER
# ==============================================================================
def main():
    # Auto-hydrate session if token exists in query_params but user profile not loaded
    if st.session_state.token and not st.session_state.user:
        ok = sync_user_profile()
        if not ok:
            st.session_state.token = None
            if "token" in st.query_params:
                del st.query_params["token"]
        else:
            refresh_conversations()
            refresh_documents()

    if not st.session_state.token:
        render_auth()
    else:
        render_sidebar()
        if st.session_state.page == "chat":
            render_chat()
        elif st.session_state.page == "documents":
            render_documents()
        elif st.session_state.page == "settings":
            render_settings()


if __name__ == "__main__":
    main()