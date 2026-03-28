import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from frontend.utils import get_student_list, api_get, track_event, inject_custom_css

st.set_page_config(page_title="Sstudize", page_icon="📚", layout="wide", initial_sidebar_state="expanded")
inject_custom_css()

DEMO_USERS = {
    "student": {"password": "student123", "role": "student", "label": "🎓 Student"},
    "teacher": {"password": "teacher123", "role": "teacher", "label": "👨‍🏫 Teacher"},
    "parent": {"password": "parent123", "role": "parent", "label": "👪 Parent"},
}

ROLE_ICONS = {"student": "🎓", "teacher": "👨‍🏫", "parent": "👪"}

if "user_role" not in st.session_state:
    st.session_state["user_role"] = None
    st.session_state["username"] = None

# ==================== LOGIN PAGE ====================
if not st.session_state["user_role"]:
    st.markdown("""
    <div style="text-align:center; padding: 2rem 0 1rem;">
        <h1 style="font-size:3rem; margin-bottom:0.2rem;">📚 Sstudize</h1>
        <p style="color:#8B949E; font-size:1.1rem;">AI-Powered Personalized Study Roadmap System</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1.2, 1.6, 1.2])
    with col2:
        st.markdown('<div style="background:#161B22; border:1px solid #30363D; border-radius:16px; padding:2rem; margin-top:1rem;">', unsafe_allow_html=True)
        st.markdown("### 🔐 Sign In")
        username = st.text_input("Username", placeholder="student / teacher / parent")
        password = st.text_input("Password", type="password", placeholder="Enter password")

        if st.button("Login", type="primary", use_container_width=True):
            user = DEMO_USERS.get(username)
            if user and user["password"] == password:
                st.session_state["user_role"] = user["role"]
                st.session_state["username"] = username
                st.rerun()
            else:
                st.error("Invalid username or password")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("")
        with st.expander("Demo Credentials"):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("**🎓 Student**\n\n`student` / `student123`")
            with c2:
                st.markdown("**👨‍🏫 Teacher**\n\n`teacher` / `teacher123`")
            with c3:
                st.markdown("**👪 Parent**\n\n`parent` / `parent123`")

    # Feature highlights
    st.markdown("")
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("#### 🤖 AI Roadmaps\nPersonalized weekly study plans powered by GPT")
    with c2:
        st.markdown("#### 📊 SWOT Analysis\nIdentify strengths, weaknesses & opportunities")
    with c3:
        st.markdown("#### 👥 Multi-Stakeholder\nTeacher & parent oversight with feedback loops")
    with c4:
        st.markdown("#### 🔄 Agent Pipeline\nAutonomous monitoring, review & adaptation")
    st.stop()

# ==================== LOGGED IN ====================
role = st.session_state["user_role"]
role_icon = ROLE_ICONS.get(role, "")

with st.sidebar:
    st.markdown(f"## 📚 Sstudize")
    st.markdown(f"{role_icon} **{st.session_state['username']}** · {role.title()}")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state["user_role"] = None
        st.session_state["username"] = None
        st.rerun()
    st.divider()

    if role in ("teacher", "student"):
        st.markdown("##### 🔑 OpenAI API Key")
        api_key = st.text_input("API key", type="password", key="api_key_input", value=st.session_state.get("api_key", ""), help="Required for AI features", label_visibility="collapsed")
        if api_key:
            st.session_state["api_key"] = api_key
            st.success("✓ Key set", icon="🔑")
        st.divider()

    st.markdown("##### 👤 Student")
    students = get_student_list()
    if students:
        student_options = {s["name"]: s["id"] for s in students}
        selected_name = st.selectbox("Student", options=list(student_options.keys()), key="student_selector", label_visibility="collapsed")
        st.session_state["selected_student_id"] = student_options[selected_name]
        st.session_state["selected_student_name"] = selected_name
        selected = next(s for s in students if s["name"] == selected_name)
        st.caption(f"📋 {selected['grade']} · {selected['exam_target']}")
        st.caption(f"📈 {selected['current_score']}/{selected['target_score']}")
    else:
        st.warning("No students found. Is the backend running?")

    st.divider()
    page_access = {
        "student": ["📋 Student Profile", "🔍 SWOT Analysis", "🗺️ Roadmap", "📊 Dashboard"],
        "teacher": ["📋 Student Profile", "🔍 SWOT Analysis", "🗺️ Roadmap", "🤖 Monitoring", "👨‍🏫 Teacher Portal", "📊 Dashboard", "📈 Clickstream", "🖥️ System Monitor"],
        "parent": ["📋 Student Profile", "👪 Parent Portal", "📊 Dashboard"],
    }
    st.markdown("##### Pages")
    for page in page_access.get(role, []):
        st.markdown(f"<span style='color:#8B949E;'>{page}</span>", unsafe_allow_html=True)

# ==================== HOME PAGE ====================
st.markdown(f"# {role_icon} Welcome, {st.session_state['username']}")
st.caption(f"{role.title()} Dashboard · Sstudize AI Study Platform")
track_event("page_view", "Home")

if st.session_state.get("selected_student_id"):
    dashboard = api_get(f"dashboard/{st.session_state['selected_student_id']}")
    if dashboard:
        st.markdown("")
        col1, col2, col3, col4 = st.columns(4)
        task_summary = dashboard.get("task_summary", {})
        with col1:
            st.metric("✅ Completed", task_summary.get("completed", 0))
        with col2:
            st.metric("⏳ Pending", task_summary.get("pending", 0))
        with col3:
            st.metric("⚠️ Overdue", task_summary.get("overdue", 0))
        with col4:
            st.metric("📊 Adherence", f"{task_summary.get('adherence_percent', 0)}%")

        student_info = dashboard.get("student", {})
        st.markdown("")
        current = student_info.get("current_score", 0)
        target = max(student_info.get("target_score", 1), 1)
        st.progress(min(current / target, 1.0), text=f"📈 Score Progress: {current} / {target}")

        # Quick actions
        st.markdown("")
        st.markdown("### ⚡ Quick Actions")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.page_link("pages/3_Roadmap.py", label="🗺️ View Roadmap", use_container_width=True)
        with c2:
            st.page_link("pages/2_SWOT_Analysis.py", label="🔍 SWOT Analysis", use_container_width=True)
        with c3:
            st.page_link("pages/7_Dashboard.py", label="📊 Full Dashboard", use_container_width=True)
