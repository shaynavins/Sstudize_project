import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from frontend.utils import api_get, api_post, api_put, get_selected_student_id, require_api_key, check_role, track_event, inject_custom_css

import json

st.set_page_config(page_title="Agent Monitoring", layout="wide")
inject_custom_css()
st.title("Agent Monitoring & Review")
track_event("page_view", "Monitoring")

check_role(["teacher"])
student_id = get_selected_student_id()
if not student_id:
    st.warning("Select a student from the sidebar.")
    st.stop()

st.subheader("Run Agents")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Run Monitoring Agent", type="primary"):
        if require_api_key():
            with st.spinner("Monitoring agent analyzing progress..."):
                result = api_post(f"monitoring/run/{student_id}")
                if result:
                    st.session_state["monitoring_result"] = result
with col2:
    if st.button("Run Review Agent"):
        if require_api_key():
            with st.spinner("Review agent generating weekly report..."):
                result = api_post(f"monitoring/review/{student_id}")
                if result:
                    st.session_state["review_result"] = result
                    st.success("Weekly report generated and saved!")
with col3:
    if st.button("Run Full Pipeline"):
        if require_api_key():
            with st.spinner("Running: Monitoring -> Review -> Roadmap (1-2 min)..."):
                result = api_post(f"monitoring/pipeline/{student_id}")
                if result:
                    st.session_state["pipeline_result"] = result
                    st.success(result.get("summary", "Pipeline complete"))

if st.session_state.get("monitoring_result"):
    st.divider()
    st.subheader("Monitoring Agent Output")
    result = st.session_state["monitoring_result"]
    if result.get("steps"):
        with st.expander("Agent Reasoning Steps"):
            for i, step in enumerate(result["steps"], 1):
                st.write(f"**Step {i}: {step['action']}**")
                st.caption(step["output"][:300])
    output = result.get("output", "")
    st.write(output[:2000])

if st.session_state.get("pipeline_result"):
    st.divider()
    st.subheader("Full Pipeline Results")
    pipeline = st.session_state["pipeline_result"]
    st.caption(f"Total time: {pipeline.get('pipeline_duration_seconds', 'N/A')}s")
    for agent_name, agent_result in pipeline.get("agents", {}).items():
        with st.expander(f"{agent_name.title()} Agent - {agent_result.get('status', 'unknown')}"):
            if agent_result.get("status") == "success":
                st.caption(f"Duration: {agent_result.get('duration_seconds', 'N/A')}s")
                st.write(agent_result.get("output", "")[:1000])
            else:
                st.error(agent_result.get("error", "Unknown error"))

st.divider()
st.subheader("Weekly Reports")
reports = api_get(f"monitoring/reports/{student_id}")
if reports:
    for report in reports:
        with st.expander(f"Week {report['week_number']} - Adherence: {report['adherence_score']}%"):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Completed", report["tasks_completed"])
            with c2:
                st.metric("Pending", report["tasks_pending"])
            with c3:
                st.metric("Overdue", report["tasks_overdue"])
            if report.get("agent_notes"):
                st.write("**Agent Analysis:**")
                st.write(report["agent_notes"])
            if report.get("recommendations"):
                st.write("**Recommendations:**")
                for rec in report["recommendations"]:
                    if isinstance(rec, dict):
                        st.write(f"- {rec.get('action', '')} ({rec.get('priority', '')})")
else:
    st.info("No weekly reports yet. Run the Review Agent to generate one.")
