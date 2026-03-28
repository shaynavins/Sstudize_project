import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from frontend.utils import api_get, api_post, api_put, get_selected_student_id, require_api_key, check_role, track_event, inject_custom_css

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Dashboard", layout="wide")
inject_custom_css()
st.title("Shared Dashboard")
track_event("page_view", "Dashboard")

check_role(["student", "teacher", "parent"])
student_id = get_selected_student_id()
if not student_id:
    st.warning("Select a student from the sidebar.")
    st.stop()

dashboard = api_get(f"dashboard/{student_id}")
if not dashboard:
    st.stop()

student_info = dashboard.get("student", {})
task_summary = dashboard.get("task_summary", {})
st.subheader(f"{student_info.get('name', '')} - {student_info.get('exam_target', '')}")

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("Current Score", student_info.get("current_score", 0))
with c2:
    st.metric("Target Score", student_info.get("target_score", 0))
with c3:
    st.metric("Adherence", f"{task_summary.get('adherence_percent', 0)}%")
with c4:
    st.metric("Tasks Done", f"{task_summary.get('completed', 0)}/{task_summary.get('total', 0)}")
with c5:
    st.metric("Pending Feedback", dashboard.get("pending_feedback_count", 0))

st.divider()
c1, c2 = st.columns(2)
with c1:
    fig = go.Figure(data=[go.Pie(labels=["Completed", "Pending", "Overdue"], values=[task_summary.get("completed", 0), task_summary.get("pending", 0), task_summary.get("overdue", 0)], marker_colors=["#4CAF50", "#FFC107", "#F44336"])])
    fig.update_layout(title="Task Status", height=350)
    st.plotly_chart(fig, use_container_width=True)
with c2:
    scores = dashboard.get("recent_scores", [])
    if scores:
        df = pd.DataFrame(scores)
        fig = px.bar(df, x="topic", y="score", color="subject", title="Recent Test Scores by Topic")
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("Performance Trends")
metrics = api_get(f"students/{student_id}/metrics")
if metrics:
    df = pd.DataFrame(metrics)
    df["date_taken"] = pd.to_datetime(df["date_taken"])
    fig = px.line(df, x="date_taken", y="score", color="subject", markers=True, title="Score Trends Over Time")
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("Feedback & Conflict Resolution")
c1, c2 = st.columns(2)
with c1:
    st.write("**Pending Feedback:**")
    pending = api_get(f"hitl/feedback/{student_id}/pending")
    if pending:
        for fb in pending:
            icon = "Teacher" if fb["source"] == "teacher" else "Parent"
            st.write(f"[{icon}] [{fb['feedback_type']}] {str(fb['content'])[:100]}...")
    else:
        st.success("No pending feedback")
with c2:
    st.write("**Conflict Resolution:**")
    if st.button("Check for Conflicts"):
        result = api_post(f"hitl/resolve-conflicts/{student_id}")
        if result:
            st.session_state["conflict_result"] = result
            if result.get("conflicts_found", 0) > 0:
                for conflict in result["conflicts"]:
                    st.warning(f"**{conflict['type']}**: {conflict['description']}")
                    st.info(f"Resolution: {conflict['resolution_detail']}")
            else:
                st.success("No conflicts detected!")
    # Show "Apply & Regenerate" if conflicts were found
    if st.session_state.get("conflict_result", {}).get("conflicts_found", 0) > 0:
        if st.button("Apply Resolutions & Regenerate Roadmap", type="primary"):
            if require_api_key():
                with st.spinner("Resolving conflicts and regenerating roadmap..."):
                    regen = api_post(f"roadmap/regenerate/{student_id}")
                    if regen:
                        st.success("Conflicts applied and roadmap regenerated!")
                        if regen.get("conflicts", {}).get("conflicts_found", 0) > 0:
                            for c in regen["conflicts"]["conflicts"]:
                                st.caption(f"{c['type']}: {c['resolution_detail']}")
                        st.session_state.pop("conflict_result", None)
                        st.rerun()

st.divider()
st.subheader("System Overview")
analytics = api_get("dashboard/analytics/summary")
health = api_get("system/health")
bottlenecks = api_get("system/bottlenecks?days=7")

if analytics:
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.metric("Students", analytics.get("total_students", 0))
    with c2:
        st.metric("Tasks", analytics.get("total_tasks", 0))
    with c3:
        st.metric("Completion", f"{analytics.get('task_completion_rate', 0)}%")
    with c4:
        st.metric("Feedback", analytics.get("total_feedback_items", 0))
    with c5:
        st.metric("Reports", analytics.get("total_weekly_reports", 0))
    with c6:
        st.metric("Agent Runs", analytics.get("agent_invocations", 0))

c1, c2 = st.columns(2)
with c1:
    if health:
        status = health.get("status", "unknown")
        color = "#4CAF50" if status == "healthy" else "#F44336"
        st.markdown(f"**System:** <span style='color:{color}'>{status.upper()}</span> | "
                    f"**Uptime:** {health.get('uptime_human', 'N/A')} | "
                    f"**DB:** {health.get('database', 'N/A')}", unsafe_allow_html=True)
with c2:
    if bottlenecks:
        agents = bottlenecks.get("agent_performance", [])
        slow_count = bottlenecks.get("slow_request_count", 0)
        if agents:
            agent_summary = " | ".join(f"{a['agent']}: {a['avg_ms']:.0f}ms" for a in agents)
            st.caption(f"Agent perf: {agent_summary}")
        if slow_count > 0:
            st.warning(f"{slow_count} slow request(s) detected in last 7 days")
        else:
            st.caption("No bottlenecks detected")
