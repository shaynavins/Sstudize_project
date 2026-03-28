from typing import Optional, Union
import streamlit as st
import requests

API_BASE = "http://localhost:7860/api"


def get_headers():
    headers = {}
    api_key = st.session_state.get("api_key")
    if api_key:
        headers["X-API-Key"] = api_key
    return headers


def api_get(endpoint):
    try:
        resp = requests.get(f"{API_BASE}/{endpoint}", headers=get_headers(), timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend. Is the FastAPI server running on port 8000?")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"API Error: {e.response.status_code}")
        return None


def api_post(endpoint, data=None):
    try:
        resp = requests.post(f"{API_BASE}/{endpoint}", json=data, headers=get_headers(), timeout=120)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend.")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"API Error: {e.response.status_code}")
        return None


def api_put(endpoint, data=None):
    try:
        resp = requests.put(f"{API_BASE}/{endpoint}", json=data, headers=get_headers(), timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend.")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"API Error: {e.response.status_code}")
        return None


def api_delete(endpoint):
    try:
        resp = requests.delete(f"{API_BASE}/{endpoint}", headers=get_headers(), timeout=30)
        resp.raise_for_status()
        return True
    except Exception:
        return False


def require_api_key():
    if not st.session_state.get("api_key"):
        st.warning("Please enter your OpenAI API key in the sidebar to use AI features.")
        return False
    return True


def get_student_list():
    result = api_get("students/")
    return result if result else []


def get_selected_student_id():
    return st.session_state.get("selected_student_id")


def check_role(allowed_roles):
    role = st.session_state.get("user_role")
    if not role:
        st.warning("Please login from the Home page.")
        st.stop()
    if role not in allowed_roles:
        st.error(f"Access denied. This page is for {', '.join(allowed_roles)} only.")
        st.stop()
    return role


# --------------- Custom Styling ---------------

def inject_custom_css():
    """Inject custom CSS to improve the look of all pages."""
    st.markdown("""
    <style>
    /* ---- Global ---- */
    .block-container { padding-top: 2rem; }
    h1 { font-weight: 700 !important; letter-spacing: -0.5px; }
    h2, h3 { font-weight: 600 !important; }

    /* ---- Metric cards ---- */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #161B22 0%, #1C2333 100%);
        border: 1px solid #30363D;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        color: #8B949E !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }

    /* ---- Sidebar ---- */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0D1117 0%, #161B22 100%) !important;
        border-right: 1px solid #21262D;
    }
    [data-testid="stSidebar"] .stTitle { font-size: 1.4rem !important; }

    /* ---- Buttons ---- */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6C63FF, #5A54D6) !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #7B73FF, #6C63FF) !important;
        box-shadow: 0 4px 12px rgba(108,99,255,0.4) !important;
    }
    .stButton > button[kind="secondary"] {
        border-radius: 8px !important;
        border: 1px solid #30363D !important;
    }

    /* ---- Expanders ---- */
    .streamlit-expanderHeader {
        background-color: #161B22 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }

    /* ---- Tabs ---- */
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        font-weight: 600;
    }

    /* ---- Dividers ---- */
    hr { border-color: #21262D !important; margin: 1.5rem 0 !important; }

    /* ---- Cards (containers) ---- */
    [data-testid="stExpander"] {
        border: 1px solid #30363D !important;
        border-radius: 12px !important;
        overflow: hidden;
    }

    /* ---- Progress bar ---- */
    .stProgress > div > div { border-radius: 8px; }

    /* ---- Form ---- */
    [data-testid="stForm"] {
        border: 1px solid #30363D !important;
        border-radius: 12px !important;
        padding: 20px !important;
        background: #161B22 !important;
    }

    /* ---- Plotly charts ---- */
    .js-plotly-plot { border-radius: 12px; overflow: hidden; }
    </style>
    """, unsafe_allow_html=True)


# --------------- Clickstream tracking ---------------

import uuid

def _get_session_id():
    """Get or create a unique session ID for clickstream tracking."""
    if "clickstream_session_id" not in st.session_state:
        st.session_state["clickstream_session_id"] = str(uuid.uuid4())[:12]
    return st.session_state["clickstream_session_id"]


def track_event(event_type, page, action=None, metadata=None):
    """Send a clickstream event to the backend (fire-and-forget)."""
    try:
        requests.post(
            f"{API_BASE}/clickstream/track",
            json={
                "event_type": event_type,
                "page": page,
                "action": action,
                "user_role": st.session_state.get("user_role", "unknown"),
                "student_id": st.session_state.get("selected_student_id"),
                "session_id": _get_session_id(),
                "metadata": metadata,
            },
            timeout=2,
        )
    except Exception:
        pass  # never block the UI for analytics
