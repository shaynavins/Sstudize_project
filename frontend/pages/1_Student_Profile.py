import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from frontend.utils import api_get, api_post, api_put, get_selected_student_id, require_api_key, check_role, track_event

import plotly.express as px
import pandas as pd

st.set_page_config(page_title="Student Profile", layout="wide")
st.title("Student Profile")
track_event("page_view", "Student Profile")

check_role(["student", "teacher", "parent"])
student_id = get_selected_student_id()
if not student_id:
    st.warning("Select a student from the sidebar.")
    st.stop()

student = api_get(f"students/{student_id}")
if not student:
    st.stop()

col1, col2 = st.columns(2)
with col1:
    st.subheader(student["name"])
    st.write(f"**Grade:** {student['grade']}")
    st.write(f"**Exam Target:** {student['exam_target']}")
    st.write(f"**Study Hours/Day:** {student['study_hours_per_day']}")
    st.write(f"**Strengths:** {', '.join(student.get('strengths', []))}")
    st.write(f"**Weaknesses:** {', '.join(student.get('weaknesses', []))}")
with col2:
    st.metric("Target Score", student["target_score"])
    st.metric("Current Score", student["current_score"])
    gap = student["target_score"] - student["current_score"]
    st.metric("Gap to Close", gap)
    subjects = student.get("subjects", {})
    if subjects:
        fig = px.bar(x=list(subjects.keys()), y=list(subjects.values()), labels={"x": "Subject", "y": "Score (%)"}, title="Subject Scores", color=list(subjects.values()), color_continuous_scale="RdYlGn")
        fig.update_layout(showlegend=False, height=300)
        st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("Performance History")
metrics = api_get(f"students/{student_id}/metrics")
if metrics:
    df = pd.DataFrame(metrics)
    df["date_taken"] = pd.to_datetime(df["date_taken"])
    fig = px.scatter(df, x="date_taken", y="score", color="subject", size="time_spent_minutes", hover_data=["topic", "test_type"], title="Score Trends Over Time")
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    with st.expander("View All Records"):
        st.dataframe(df[["subject", "topic", "score", "test_type", "date_taken", "time_spent_minutes"]], use_container_width=True)
else:
    st.info("No performance data yet.")

st.divider()
st.subheader("Add Test Score")
with st.form("add_metric"):
    c1, c2, c3 = st.columns(3)
    with c1:
        subject = st.text_input("Subject", placeholder="Physics")
        topic = st.text_input("Topic", placeholder="Thermodynamics")
    with c2:
        score = st.number_input("Score (%)", 0.0, 100.0, 75.0)
        test_type = st.selectbox("Test Type", ["practice", "mock", "assignment"])
    with c3:
        time_spent = st.number_input("Time Spent (minutes)", 0, 300, 30)
    if st.form_submit_button("Add Score"):
        result = api_post(f"students/{student_id}/metrics", {"student_id": student_id, "subject": subject, "topic": topic, "score": score, "test_type": test_type, "time_spent_minutes": time_spent})
        if result:
            st.success("Score added!")
            st.rerun()
