import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from frontend.utils import get_student_list, api_get, track_event

st.set_page_config(page_title="Sstudize", page_icon="S", layout="wide", initial_sidebar_state="expanded")

DEMO_USERS = {
    "student": {"password": "student123", "role": "student", "label": "Student"},
    "teacher": {"password": "teacher123", "role": "teacher", "label": "Teacher"},
    "parent": {"password": "parent123", "role": "parent", "label": "Parent"},
}

if "user_role" not in st.session_state:
    st.session_state["user_role"] = None
    st.session_state["username"] = None

if not st.session_state["user_role"]:
    st.title("Sstudize - Login")
    st.caption("AI-Powered Study Roadmap System")
    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("Sign In")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login", type="primary", use_container_width=True):
            user = DEMO_USERS.get(username)
            if user and user["password"] == password:
                st.session_state["user_role"] = user["role"]
                st.session_state["username"] = username
                st.rerun()
            else:
                st.error("Invalid username or password")

        st.divider()
        st.caption("Demo credentials:")
        st.code("student / student123\nteacher / teacher123\nparent  / parent123")
    st.stop()

role = st.session_state["user_role"]

with st.sidebar:
    st.title("Sstudize")
    st.caption(f"Logged in as: **{st.session_state['username']}** ({role})")
    if st.button("Logout"):
        st.session_state["user_role"] = None
        st.session_state["username"] = None
        st.rerun()
    st.divider()

    if role in ("teacher", "student"):
        st.subheader("OpenAI API Key")
        api_key = st.text_input("Enter your API key", type="password", key="api_key_input", value=st.session_state.get("api_key", ""), help="Required for AI features")
        if api_key:
            st.session_state["api_key"] = api_key
            st.success("API key set")
        st.divider()

    st.subheader("Select Student")
    students = get_student_list()
    if students:
        student_options = {s["name"]: s["id"] for s in students}
        selected_name = st.selectbox("Student", options=list(student_options.keys()), key="student_selector")
        st.session_state["selected_student_id"] = student_options[selected_name]
        st.session_state["selected_student_name"] = selected_name
        selected = next(s for s in students if s["name"] == selected_name)
        st.caption(f"Grade: {selected['grade']} | Target: {selected['exam_target']}")
        st.caption(f"Score: {selected['current_score']}/{selected['target_score']}")
    else:
        st.warning("No students found. Is the backend running?")

    st.divider()
    st.caption("Your pages:")
    page_access = {
        "student": ["Student Profile", "SWOT Analysis", "Roadmap", "Dashboard"],
        "teacher": ["Student Profile", "SWOT Analysis", "Roadmap", "Monitoring", "Teacher Portal", "Dashboard", "Clickstream Analytics", "System Monitor"],
        "parent": ["Student Profile", "Parent Portal", "Dashboard"],
    }
    for page in page_access.get(role, []):
        st.write(f"- {page}")

st.title(f"Sstudize - {role.title()} View")
track_event("page_view", "Home")

if st.session_state.get("selected_student_id"):
    dashboard = api_get(f"dashboard/{st.session_state['selected_student_id']}")
    if dashboard:
        col1, col2, col3, col4 = st.columns(4)
        task_summary = dashboard.get("task_summary", {})
        with col1:
            st.metric("Tasks Completed", task_summary.get("completed", 0))
        with col2:
            st.metric("Tasks Pending", task_summary.get("pending", 0))
        with col3:
            st.metric("Tasks Overdue", task_summary.get("overdue", 0))
        with col4:
            st.metric("Adherence", f"{task_summary.get('adherence_percent', 0)}%")
        student_info = dashboard.get("student", {})
        st.progress(min(student_info.get("current_score", 0) / max(student_info.get("target_score", 1), 1), 1.0), text=f"Current: {student_info.get('current_score', 0)} / Target: {student_info.get('target_score', 0)}")
