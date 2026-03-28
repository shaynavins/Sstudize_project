import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from frontend.utils import api_get, api_post, api_put, get_selected_student_id, require_api_key, check_role, track_event

st.set_page_config(page_title="SWOT Analysis", layout="wide")
st.title("SWOT Analysis")
track_event("page_view", "SWOT Analysis")

check_role(["student", "teacher"])
student_id = get_selected_student_id()
if not student_id:
    st.warning("Select a student from the sidebar.")
    st.stop()

col1, col2 = st.columns([1, 3])
with col1:
    if st.button("Generate SWOT", type="primary"):
        if require_api_key():
            with st.spinner("Analyzing student data with GPT..."):
                result = api_post(f"roadmap/swot/{student_id}")
                if result:
                    st.success("SWOT analysis generated!")
                    st.rerun()

swot = api_get(f"roadmap/swot/{student_id}")
if not swot:
    st.info("No SWOT analysis yet. Click Generate SWOT to create one.")
    st.stop()

st.caption(f"Generated: {swot.get('created_at', 'Unknown')}")
col1, col2 = st.columns(2)
with col1:
    st.markdown("### Strengths")
    for item in swot.get("strengths", []):
        if isinstance(item, dict):
            st.success(f"**{item.get('area', '')}**: {item.get('detail', '')}")
        else:
            st.success(str(item))
    st.markdown("### Opportunities")
    for item in swot.get("opportunities", []):
        if isinstance(item, dict):
            st.info(f"**{item.get('area', '')}**: {item.get('detail', '')}")
        else:
            st.info(str(item))
with col2:
    st.markdown("### Weaknesses")
    for item in swot.get("weaknesses", []):
        if isinstance(item, dict):
            st.warning(f"**{item.get('area', '')}**: {item.get('detail', '')}")
        else:
            st.warning(str(item))
    st.markdown("### Challenges")
    for item in swot.get("challenges", []):
        if isinstance(item, dict):
            st.error(f"**{item.get('area', '')}**: {item.get('detail', '')}")
        else:
            st.error(str(item))

st.divider()
st.subheader("Action Plan")
for i, action in enumerate(swot.get("action_plan", []), 1):
    if isinstance(action, dict):
        priority = action.get("priority", "medium")
        st.write(f"**{i}.** {action.get('action', '')} ({priority})")
    else:
        st.write(f"**{i}.** {action}")
