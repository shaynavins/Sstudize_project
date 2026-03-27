import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from frontend.utils import api_get, api_post, api_put, get_selected_student_id, require_api_key, check_role

st.set_page_config(page_title="Parent Portal", layout="wide")
st.title("Parent Portal")

check_role(["parent"])
student_id = get_selected_student_id()
if not student_id:
    st.warning("Select a student from the sidebar.")
    st.stop()

st.subheader("Progress Summary")
dashboard = api_get(f"dashboard/{student_id}")
if dashboard:
    student_info = dashboard.get("student", {})
    st.write(f"**{student_info.get('name', '')}** - Grade {student_info.get('grade', '')} | {student_info.get('exam_target', '')}")
    c1, c2, c3, c4 = st.columns(4)
    task_summary = dashboard.get("task_summary", {})
    with c1:
        st.metric("Tasks Done", task_summary.get("completed", 0))
    with c2:
        st.metric("Pending", task_summary.get("pending", 0))
    with c3:
        st.metric("Overdue", task_summary.get("overdue", 0))
    with c4:
        st.metric("Adherence", f"{task_summary.get('adherence_percent', 0)}%")
    current = student_info.get("current_score", 0)
    target = student_info.get("target_score", 1)
    st.progress(min(current / max(target, 1), 1.0), text=f"Score: {current} / {target}")

st.divider()
st.subheader("Submit Observation")
with st.form("parent_observation"):
    c1, c2 = st.columns(2)
    with c1:
        stress_level = st.slider("Stress Level", 1, 5, 3, help="1=Low, 5=Very High")
        study_pattern = st.selectbox("Study Pattern", ["consistent", "irregular", "declining"])
        sleep_hours = st.number_input("Sleep Hours (per night)", 4.0, 12.0, 7.0, step=0.5)
    with c2:
        distractions = st.multiselect("Observed Distractions", ["Phone", "Social Media", "Gaming", "TV", "Friends", "Other"])
        health_issues = st.text_input("Health Issues (leave blank if none)")
        notes = st.text_area("Additional Notes", height=100)
    if st.form_submit_button("Submit Observation", type="primary"):
        content = {"stress_level": stress_level, "study_pattern": study_pattern, "sleep_hours": sleep_hours, "distractions": distractions, "health_issues": health_issues if health_issues else None, "additional_notes": notes}
        result = api_post("hitl/feedback", {"student_id": student_id, "source": "parent", "feedback_type": "observation", "content": content})
        if result:
            st.success("Observation submitted!")

st.divider()
st.subheader("Request Goal Adjustment")
with st.form("goal_adjustment"):
    adj_type = st.selectbox("Adjustment Type", ["reduce_load", "change_schedule", "extend_deadline", "add_break"])
    reason = st.selectbox("Reason", ["burnout", "health", "family_event", "exams_at_school", "other"])
    details = st.text_area("Details", placeholder="Explain the adjustment needed...")
    duration = st.number_input("Duration (days)", 1, 30, 7)
    if st.form_submit_button("Request Adjustment"):
        content = {"adjustment_type": adj_type, "reason": reason, "details": details, "duration_days": duration}
        result = api_post("hitl/feedback", {"student_id": student_id, "source": "parent", "feedback_type": "goal_adjustment", "content": content})
        if result:
            st.success("Adjustment request submitted!")
