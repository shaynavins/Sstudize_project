import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from frontend.utils import api_get, api_post, api_put, get_selected_student_id, require_api_key

st.set_page_config(page_title="Study Roadmap", layout="wide")
st.title("Study Roadmap")

student_id = get_selected_student_id()
if not student_id:
    st.warning("Select a student from the sidebar.")
    st.stop()

col1, col2 = st.columns(2)
with col1:
    if st.button("Generate Roadmap (Direct)", type="primary"):
        if require_api_key():
            with st.spinner("Generating roadmap with GPT..."):
                result = api_post(f"roadmap/generate/{student_id}")
                if result:
                    st.success("Roadmap generated!")
                    st.rerun()
with col2:
    if st.button("Generate Roadmap (Agent)"):
        if require_api_key():
            with st.spinner("Running Roadmap Agent (30-60s)..."):
                result = api_post(f"roadmap/agent-generate/{student_id}")
                if result:
                    st.success("Agent-generated roadmap ready!")
                    if result.get("steps"):
                        with st.expander("Agent Reasoning Steps"):
                            for step in result["steps"]:
                                st.write(f"**{step['action']}** -> {step['output'][:200]}...")

st.divider()
st.subheader("Study Tasks")
tasks = api_get(f"roadmap/tasks/{student_id}")
if not tasks:
    st.info("No tasks yet. Generate a roadmap to create study tasks.")
    st.stop()

completed = [t for t in tasks if t["completed"]]
pending = [t for t in tasks if not t["completed"]]
tab1, tab2 = st.tabs([f"Pending ({len(pending)})", f"Completed ({len(completed)})"])

with tab1:
    for task in pending:
        with st.container():
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            with c1:
                st.write(f"**{task['subject']} - {task['topic']}**")
                st.caption(task["description"])
                if task.get("resources"):
                    for r in task["resources"]:
                        if isinstance(r, dict) and r.get("title"):
                            st.caption(f"Resource: {r['title']}")
            with c2:
                st.caption(f"Type: {task['task_type']}")
            with c3:
                st.caption(f"Est: {task['estimated_hours']}h")
            with c4:
                if st.button("Done", key=f"complete_{task['id']}"):
                    api_put(f"roadmap/tasks/{task['id']}/complete")
                    st.rerun()
            st.divider()

with tab2:
    for task in completed:
        st.write(f"~~{task['subject']} - {task['topic']}: {task['description']}~~")

st.divider()
with st.expander("Roadmap History"):
    roadmaps = api_get(f"roadmap/{student_id}")
    if roadmaps:
        for rm in roadmaps:
            st.write(f"Week {rm['week_number']} ({rm['start_date']} to {rm['end_date']}) - Status: {rm['status']} - Approved: {rm['approved_by_teacher']}")
            if rm.get("goals"):
                for g in rm["goals"]:
                    st.caption(f"  - {g}")
    else:
        st.info("No roadmap history yet.")
