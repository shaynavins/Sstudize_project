import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from frontend.utils import get_student_list, api_get

st.set_page_config(page_title="Sstudize", page_icon="S", layout="wide", initial_sidebar_state="expanded")

with st.sidebar:
    st.title("Sstudize")
    st.caption("AI-Powered Study Roadmap System")
    st.divider()
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

st.title("Sstudize - Personalized Study Roadmap System")
st.markdown("""
### System Architecture
- **AI Layer**: OpenAI GPT for SWOT analysis and roadmap generation
- **Agents**: LangGraph ReAct agents for autonomous monitoring and review
- **HITL**: Teacher and parent feedback loops with conflict resolution
- **Backend**: FastAPI REST API with SQLite database
- **Frontend**: Streamlit multi-page application
""")

if st.session_state.get("selected_student_id"):
    st.divider()
    st.subheader(f"Overview for {st.session_state.get('selected_student_name', '')}")
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
