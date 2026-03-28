import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from frontend.utils import api_get, check_role, track_event

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Clickstream Analytics", layout="wide")
st.title("Clickstream Analytics")
track_event("page_view", "Clickstream Analytics")

check_role(["teacher"])

# Controls
days = st.selectbox("Time period", [1, 7, 14, 30], index=1, format_func=lambda d: f"Last {d} day(s)")

# Fetch data
data = api_get(f"clickstream/analytics?days={days}")
flow_data = api_get(f"clickstream/analytics/flow?days={days}")

if not data or data.get("total_events", 0) == 0:
    st.info("No clickstream data yet. Browse the app to generate events, then come back here.")
    st.stop()

# --------------- KPI Row ---------------
st.subheader("Overview")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Total Events", data["total_events"])
with c2:
    st.metric("Unique Sessions", data["session_count"])
with c3:
    st.metric("Pages Tracked", len(data.get("page_views", {})))
with c4:
    top_page = max(data.get("page_views", {}), key=data["page_views"].get, default="N/A")
    st.metric("Most Visited Page", top_page)

# --------------- Page Views Chart ---------------
st.divider()
st.subheader("Page Views")
page_views = data.get("page_views", {})
if page_views:
    c1, c2 = st.columns(2)
    with c1:
        df = pd.DataFrame({"Page": list(page_views.keys()), "Views": list(page_views.values())})
        fig = px.bar(df, x="Page", y="Views", color="Views", color_continuous_scale="Blues", title="Page View Distribution")
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = go.Figure(data=[go.Pie(labels=list(page_views.keys()), values=list(page_views.values()))])
        fig.update_layout(title="Page View Share", height=350)
        st.plotly_chart(fig, use_container_width=True)

# --------------- User Role Breakdown ---------------
st.divider()
st.subheader("User Activity by Role")
roles = data.get("user_roles", {})
if roles:
    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure(data=[go.Bar(x=list(roles.keys()), y=list(roles.values()), marker_color=["#4CAF50", "#2196F3", "#FF9800"][:len(roles)])])
        fig.update_layout(title="Events by User Role", height=300)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        # Hourly distribution
        hourly = data.get("hourly_distribution", {})
        if hourly:
            hours = [int(h) for h in hourly.keys()]
            counts = list(hourly.values())
            fig = px.line(x=hours, y=counts, markers=True, labels={"x": "Hour of Day", "y": "Events"}, title="Activity by Hour")
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

# --------------- Top Actions ---------------
st.divider()
st.subheader("Top Actions")
top_actions = data.get("top_actions", [])
if top_actions:
    df = pd.DataFrame(top_actions)
    fig = px.bar(df, x="action", y="count", color="count", color_continuous_scale="Viridis", title="Most Frequent Actions")
    fig.update_layout(height=350, xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No specific actions tracked yet.")

# --------------- Engagement by Page ---------------
st.divider()
st.subheader("Engagement by Page")
engagement = data.get("engagement_by_page", {})
if engagement:
    df = pd.DataFrame({"Page": list(engagement.keys()), "Total Interactions": list(engagement.values())})
    fig = px.bar(df, x="Page", y="Total Interactions", color="Total Interactions", color_continuous_scale="RdYlGn", title="Total Interactions per Page")
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)

# --------------- User Flow (Page Transitions) ---------------
st.divider()
st.subheader("User Navigation Flow")
if flow_data and flow_data.get("transitions"):
    transitions = flow_data["transitions"]

    # Sankey diagram
    pages = list(set([t["from"] for t in transitions] + [t["to"] for t in transitions]))
    page_idx = {p: i for i, p in enumerate(pages)}

    fig = go.Figure(data=[go.Sankey(
        node=dict(label=pages, color=["#2196F3"] * len(pages)),
        link=dict(
            source=[page_idx[t["from"]] for t in transitions],
            target=[page_idx[t["to"]] for t in transitions],
            value=[t["count"] for t in transitions],
        ),
    )])
    fig.update_layout(title="Page Navigation Flow (Sankey)", height=450)
    st.plotly_chart(fig, use_container_width=True)

    # Entry pages
    entry = flow_data.get("entry_pages", {})
    if entry:
        st.write("**Entry Pages** (first page users land on):")
        for page, count in entry.items():
            st.write(f"- {page}: {count} session(s)")
else:
    st.info("Not enough navigation data for flow analysis yet.")

# --------------- Raw Event Log ---------------
st.divider()
with st.expander("Raw Clickstream Data"):
    st.caption(f"Period: last {days} day(s) | Total: {data['total_events']} events | Sessions: {data['session_count']}")
    st.json(data)
