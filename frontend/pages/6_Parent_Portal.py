import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from frontend.utils import api_get, api_post, api_put, get_selected_student_id, require_api_key, check_role, track_event, inject_custom_css

st.set_page_config(page_title="Parent Portal", layout="wide")
inject_custom_css()
st.title("Parent Portal")
track_event("page_view", "Parent Portal")

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
st.subheader("Current Study Plan")
roadmaps = api_get(f"roadmap/{student_id}")
if roadmaps:
    latest = roadmaps[0]
    st.write(f"**Week {latest['week_number']}** ({latest['start_date']} to {latest['end_date']})")
    approved = "Approved by teacher" if latest["approved_by_teacher"] else "Awaiting teacher review"
    st.caption(f"Status: {latest['status']} | {approved}")
    if latest.get("goals"):
        for g in latest["goals"]:
            st.write(f"  - {g}")
    tasks = api_get(f"roadmap/tasks/{student_id}")
    if tasks:
        pending_tasks = [t for t in tasks if not t["completed"]]
        done_tasks = [t for t in tasks if t["completed"]]
        if pending_tasks:
            with st.expander(f"Upcoming tasks ({len(pending_tasks)})"):
                for t in pending_tasks:
                    st.write(f"- **{t['subject']}** / {t['topic']}: {t['description']} ({t['priority']}, {t['estimated_hours']}h)")
        if done_tasks:
            st.success(f"{len(done_tasks)} task(s) completed!")
else:
    st.info("No study plan generated yet.")

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
            # Show processing flags from the backend
            proc = result.get("content", {}).get("_processing", {})
            if proc.get("priority") == "high":
                st.warning("Your observation was flagged as **urgent**. The teacher will be notified.")
                if proc.get("flags"):
                    st.caption(f"Flags: {', '.join(proc['flags'])}")
                if proc.get("recommend_load_reduction"):
                    st.info("Recommendation: Study load reduction suggested based on high stress.")
            else:
                st.success("Observation submitted and processed!")

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
            proc = result.get("content", {}).get("_processing", {})
            if proc.get("priority") == "high":
                st.warning("Adjustment request marked as **urgent** due to health/burnout concern.")
            else:
                st.success("Adjustment request submitted!")

st.divider()
st.subheader("My Feedback History")
my_feedback = api_get(f"hitl/feedback/{student_id}?source=parent")
if my_feedback:
    for fb in my_feedback:
        status_label = "Applied" if fb["resolved"] else ("Urgent" if fb.get("status") == "urgent" else "Pending")
        icon = "🔴" if fb.get("status") == "urgent" and not fb["resolved"] else ("✅" if fb["resolved"] else "🟡")
        with st.expander(f"{icon} [{fb['feedback_type']}] {status_label} - {fb['created_at'][:10]}"):
            content = fb.get("content", {})
            display = {k: v for k, v in content.items() if k != "_processing"}
            for k, v in display.items():
                st.write(f"**{k.replace('_', ' ').title()}:** {v}")
            proc = content.get("_processing", {})
            if proc:
                st.caption(f"Priority: {proc.get('priority', 'N/A')} | Flags: {', '.join(proc.get('flags', []))}")
else:
    st.info("No feedback submitted yet.")
