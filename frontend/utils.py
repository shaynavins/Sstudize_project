from typing import Optional, Union
import streamlit as st
import requests

API_BASE = "http://localhost:8000/api"


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
