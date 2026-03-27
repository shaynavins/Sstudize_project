import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from frontend.utils import api_get, api_post, api_put, get_selected_student_id, require_api_key, check_role

st.set_page_config(page_title="Teacher Portal", layout="wide")
st.title("Teacher Portal")

check_role(["teacher"])
student_id = get_selected_student_id()
if not student_id:
    st.warning("Select a student from the sidebar.")
    st.stop()

st.subheader("Roadmap Review")
roadmaps = api_get(f"roadmap/{student_id}")
if roadmaps:
    latest = roadmaps[0]
    st.write(f"**Week {latest['week_number']}** ({latest['start_date']} to {latest['end_date']})")
    st.write(f"Status: {latest['status']} | Approved: {'Yes' if latest['approved_by_teacher'] else 'Pending'}")
    if latest.get("goals"):
        st.write("**Goals:**")
        for g in latest["goals"]:
            st.write(f"  - {g}")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Approve Roadmap", type="primary"):
            api_put(f"hitl/roadmap/{latest['id']}/approve")
            st.success("Roadmap approved!")
            st.rerun()
    with c2:
        if st.button("Reject Roadmap"):
            api_put(f"hitl/roadmap/{latest['id']}/reject")
            st.warning("Roadmap rejected.")
            st.rerun()
else:
    st.info("No roadmaps to review yet.")

st.divider()
st.subheader("Submit Feedback")
with st.form("teacher_feedback"):
    feedback_type = st.selectbox("Feedback Type", ["roadmap_review", "task_modification", "observation", "goal_adjustment"])
    c1, c2 = st.columns(2)
    with c1:
        notes = st.text_area("Notes / Comments", height=150)
        focus_areas = st.text_input("Recommended Focus Areas (comma-separated)")
    with c2:
        class_participation = st.selectbox("Class Participation", ["good", "average", "poor"])
        assignment_quality = st.selectbox("Assignment Quality", ["good", "average", "poor"])
        non_academic = st.text_input("Non-academic Concerns (optional)")
    if st.form_submit_button("Submit Feedback", type="primary"):
        content = {"notes": notes, "class_participation": class_participation, "assignment_quality": assignment_quality, "recommended_focus_areas": [a.strip() for a in focus_areas.split(",") if a.strip()], "non_academic_concerns": non_academic if non_academic else None}
        result = api_post("hitl/feedback", {"student_id": student_id, "source": "teacher", "feedback_type": feedback_type, "content": content})
        if result:
            st.success("Feedback submitted!")

st.divider()
with st.expander("Feedback History"):
    feedbacks = api_get(f"hitl/feedback/{student_id}?source=teacher")
    if feedbacks:
        for fb in feedbacks:
            status = "Applied" if fb["resolved"] else "Pending"
            st.write(f"[{fb['feedback_type']}] {status} - {fb['created_at'][:10]}")
            st.caption(str(fb["content"])[:200])
    else:
        st.info("No teacher feedback yet.")
