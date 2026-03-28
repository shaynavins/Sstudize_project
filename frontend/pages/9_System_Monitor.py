import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from frontend.utils import api_get, check_role, track_event

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="System Monitor", layout="wide")
st.title("System Monitor")
track_event("page_view", "System Monitor")

check_role(["teacher"])

days = st.selectbox("Time period", [1, 7, 14, 30], index=1, format_func=lambda d: f"Last {d} day(s)")

# --------------- Health Status ---------------
st.subheader("System Health")
health = api_get("system/health")
if health:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        color = "normal" if health["status"] == "healthy" else "off"
        st.metric("Status", health["status"].upper())
    with c2:
        st.metric("Database", health["database"])
    with c3:
        st.metric("Uptime", health["uptime_human"])
    with c4:
        st.metric("PID", health["pid"])

# --------------- API Performance ---------------
st.divider()
st.subheader("API Performance")
perf = api_get(f"system/performance?days={days}")
if perf and perf.get("total_requests", 0) > 0:
    overall = perf.get("overall", {})
    status_bd = perf.get("status_breakdown", {})

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Total Requests", perf["total_requests"])
    with c2:
        st.metric("Avg Response", f"{overall.get('avg_ms', 0):.0f}ms")
    with c3:
        st.metric("P95 Response", f"{overall.get('p95_ms', 0):.0f}ms")
    with c4:
        st.metric("Max Response", f"{overall.get('max_ms', 0):.0f}ms")
    with c5:
        error_pct = (status_bd.get("4xx", 0) + status_bd.get("5xx", 0)) / max(perf["total_requests"], 1) * 100
        st.metric("Error Rate", f"{error_pct:.1f}%")

    # Status breakdown pie
    c1, c2 = st.columns(2)
    with c1:
        if status_bd:
            fig = go.Figure(data=[go.Pie(
                labels=list(status_bd.keys()), values=list(status_bd.values()),
                marker_colors=["#4CAF50", "#FFC107", "#F44336"][:len(status_bd)],
            )])
            fig.update_layout(title="Response Status Breakdown", height=300)
            st.plotly_chart(fig, use_container_width=True)

    # Endpoint response times
    with c2:
        endpoints = perf.get("endpoints", [])
        if endpoints:
            df = pd.DataFrame(endpoints[:10])
            fig = px.bar(df, x="path", y="avg_ms", color="max_ms",
                         color_continuous_scale="YlOrRd",
                         title="Avg Response Time by Endpoint (ms)")
            fig.update_layout(height=300, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

    # Full endpoint table
    if endpoints:
        with st.expander("All Endpoint Metrics"):
            df = pd.DataFrame(endpoints)
            st.dataframe(df, use_container_width=True)
else:
    st.info("No API performance data yet.")

# --------------- Bottlenecks ---------------
st.divider()
st.subheader("Bottlenecks & Agent Performance")
bottlenecks = api_get(f"system/bottlenecks?days={days}")
if bottlenecks:
    c1, c2 = st.columns(2)

    with c1:
        st.write("**Slow Requests (>2s)**")
        slow = bottlenecks.get("slow_requests", [])
        if slow:
            for s in slow[:10]:
                st.warning(f"`{s['method']} {s['path']}` — **{s['duration_ms']:.0f}ms** ({s['timestamp'][:19]})")
        else:
            st.success("No slow requests detected!")

    with c2:
        st.write("**Agent Performance**")
        agents = bottlenecks.get("agent_performance", [])
        if agents:
            for a in agents:
                success_rate = a["successes"] / max(a["total_runs"], 1) * 100
                st.write(f"**{a['agent'].title()}**: {a['total_runs']} runs | "
                         f"{success_rate:.0f}% success | Avg: {a['avg_ms']:.0f}ms | Max: {a['max_ms']:.0f}ms")
            # Agent chart
            df = pd.DataFrame(agents)
            fig = px.bar(df, x="agent", y="avg_ms", color="failures",
                         color_continuous_scale="RdYlGn_r",
                         title="Agent Avg Response Time (ms)")
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No agent runs recorded yet.")

# --------------- Error Log ---------------
st.divider()
st.subheader("Error Log")
errors = api_get(f"system/errors?days={days}")
if errors and errors.get("total_errors", 0) > 0:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Total Errors", errors["total_errors"])
        by_endpoint = errors.get("errors_by_endpoint", {})
        if by_endpoint:
            st.write("**Errors by Endpoint:**")
            for path, count in by_endpoint.items():
                st.write(f"- `{path}`: {count}")

    with c2:
        if by_endpoint:
            fig = px.bar(x=list(by_endpoint.keys()), y=list(by_endpoint.values()),
                         labels={"x": "Endpoint", "y": "Errors"},
                         title="Errors by Endpoint", color=list(by_endpoint.values()),
                         color_continuous_scale="Reds")
            fig.update_layout(height=300, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

    # Error details
    for err in errors.get("errors", [])[:10]:
        with st.expander(f"{err['status']} — {err['method']} {err['path']} ({err['timestamp'][:19]})"):
            st.write(f"**Duration:** {err.get('duration_ms', 0):.0f}ms")
            if err.get("traceback"):
                st.code(err["traceback"][:1500], language="python")
            else:
                st.caption("No traceback available")
else:
    st.success("No errors in the selected period!")
