import streamlit as st
import sys
import requests
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from frontend.utils import api_get, api_post, api_put, get_selected_student_id, require_api_key, check_role, get_headers, API_BASE, track_event

st.set_page_config(page_title="Teacher Portal", layout="wide")
st.title("Teacher Portal")
track_event("page_view", "Teacher Portal")

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
    status_label = latest["status"]
    approved_label = "Approved" if latest["approved_by_teacher"] else ("Rejected" if latest["status"] == "rejected" else "Pending")
    st.write(f"Status: {status_label} | Teacher: {approved_label}")
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
        reject_expanded = st.expander("Reject Roadmap", expanded=False)
        with reject_expanded:
            reject_reason = st.text_area("Rejection reason", key="reject_reason", placeholder="Explain why the roadmap needs changes...")
            auto_regen = st.checkbox("Auto-regenerate with feedback", value=True, key="auto_regen")
            if st.button("Confirm Rejection", type="secondary"):
                if require_api_key():
                    # Use requests directly since we need to send a JSON body with PUT
                    try:
                        resp = requests.put(
                            f"{API_BASE}/hitl/roadmap/{latest['id']}/reject",
                            json={"reason": reject_reason, "auto_regenerate": auto_regen},
                            headers=get_headers(),
                            timeout=120,
                        )
                        resp.raise_for_status()
                        result = resp.json()
                        if result.get("regenerated"):
                            st.success("Roadmap rejected and new roadmap generated with your feedback!")
                        else:
                            st.warning("Roadmap rejected. Feedback saved.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
else:
    st.info("No roadmaps to review yet.")

st.divider()
st.subheader("Task Review")
tasks = api_get(f"roadmap/tasks/{student_id}")
if tasks:
    pending_tasks = [t for t in tasks if not t["completed"]]
    if pending_tasks:
        for task in pending_tasks:
            with st.expander(f"{task['subject']} - {task['topic']} ({task['priority']} | {task['estimated_hours']}h)"):
                st.write(task["description"])
                if task.get("resources"):
                    for r in task["resources"]:
                        if isinstance(r, dict) and r.get("title"):
                            st.caption(f"Resource: {r['title']}")
                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.button("Approve", key=f"approve_task_{task['id']}"):
                        api_put(f"hitl/task/{task['id']}/review", {"action": "approve"})
                        st.success("Task approved")
                with c2:
                    mod_notes = st.text_input("Modification", key=f"mod_{task['id']}", placeholder="Change description...")
                    new_priority = st.selectbox("Priority", ["high", "medium", "low"], key=f"pri_{task['id']}", index=["high", "medium", "low"].index(task["priority"]))
                    new_hours = st.number_input("Hours", value=task["estimated_hours"], min_value=0.5, step=0.5, key=f"hrs_{task['id']}")
                    if st.button("Apply Changes", key=f"modify_task_{task['id']}"):
                        api_put(f"hitl/task/{task['id']}/review", {
                            "action": "modify",
                            "modification_notes": mod_notes,
                            "new_priority": new_priority,
                            "new_estimated_hours": new_hours,
                        })
                        st.success("Task modified")
                        st.rerun()
                with c3:
                    if st.button("Remove Task", key=f"remove_task_{task['id']}"):
                        api_put(f"hitl/task/{task['id']}/review", {"action": "remove"})
                        st.warning("Task removed")
                        st.rerun()
    else:
        st.info("All tasks completed or no tasks found.")
else:
    st.info("No tasks to review. Generate a roadmap first.")

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
            st.success("Feedback submitted and processed!")

st.divider()
st.subheader("Parent Feedback (for awareness)")
parent_feedback = api_get(f"hitl/feedback/{student_id}?source=parent")
if parent_feedback:
    urgent = [f for f in parent_feedback if f.get("status") == "urgent" and not f["resolved"]]
    if urgent:
        st.error(f"{len(urgent)} urgent parent concern(s) require attention:")
        for fb in urgent:
            content = fb.get("content", {})
            st.warning(f"**{fb['feedback_type']}** - Stress: {content.get('stress_level', 'N/A')}/5 | "
                       f"Pattern: {content.get('study_pattern', 'N/A')} | "
                       f"Health: {content.get('health_issues', 'None')}")
            if content.get('additional_notes'):
                st.caption(content['additional_notes'])
    pending_parent = [f for f in parent_feedback if not f["resolved"] and f not in urgent]
    if pending_parent:
        with st.expander(f"{len(pending_parent)} pending parent observation(s)"):
            for fb in pending_parent:
                st.write(f"[{fb['feedback_type']}] {fb['created_at'][:10]}")
                st.caption(str(fb["content"])[:200])
    if not urgent and not pending_parent:
        st.success("No pending parent feedback.")
else:
    st.info("No parent feedback yet.")

st.divider()
with st.expander("My Feedback History"):
    feedbacks = api_get(f"hitl/feedback/{student_id}?source=teacher")
    if feedbacks:
        for fb in feedbacks:
            status_icon = "applied" if fb["resolved"] else ("urgent" if fb.get("status") == "urgent" else "pending")
            st.write(f"[{fb['feedback_type']}] {status_icon} - {fb['created_at'][:10]}")
            st.caption(str(fb["content"])[:200])
    else:
        st.info("No teacher feedback yet.")
