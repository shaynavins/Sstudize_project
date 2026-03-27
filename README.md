---
title: Sstudize
emoji: 📚
colorFrom: blue
colorTo: green
sdk: docker
app_port: 8501
pinned: false
---

# 📚 Sstudize — Personalized Study Roadmap System

An AI-driven personalized study roadmap system for competitive exam preparation (JEE/NEET), featuring agentic AI monitoring, human-in-the-loop oversight, and multi-stakeholder dashboards.

## Architecture

- **Frontend**: Streamlit (multi-page app with 7 pages)
- **Backend**: FastAPI (REST API)
- **AI Layer**: OpenAI GPT (SWOT analysis, roadmap generation)
- **Agents**: LangChain ReAct agents (monitoring, review, roadmap planning)
- **Database**: SQLite
- **Analytics**: Custom clickstream logging
- **Deployment**: HuggingFace Spaces (Docker)

## Features

### AI-Driven Roadmap Generation
- Personalized weekly study plans based on SWOT analysis and exam trends
- Dynamic updates based on performance data and feedback
- Two generation modes: Direct (fast) and Agent-based (autonomous)

### Multi-Agent Monitoring System
- **Monitoring Agent**: Tracks task completion, flags deviations
- **Review Agent**: Generates weekly reports, sends notifications
- **Roadmap Agent**: Autonomously gathers context and creates study plans
- Full pipeline: Monitoring → Review → Roadmap (sequential orchestration)

### Human-in-the-Loop (HITL)
- **Teacher Portal**: Roadmap review, approval/rejection, feedback submission
- **Parent Portal**: Progress monitoring, stress/distraction reporting, goal adjustments
- **Conflict Resolution**: Automatic detection and resolution of teacher-parent conflicts

### Shared Dashboard
- Real-time progress tracking with Plotly charts
- Stakeholder comments and coordination
- System-wide analytics

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Terminal 1: Start backend
uvicorn backend.main:app --reload --port 8000

# Terminal 2: Start frontend
streamlit run frontend/app.py
```

Then open http://localhost:8501 and enter your OpenAI API key in the sidebar.

## Project Structure

```
Sstudize/
├── frontend/          # Streamlit UI (app.py + 7 pages)
├── backend/           # FastAPI REST API
├── agents/            # LangChain ReAct agents + tools
├── core/              # AI layer (LLM, SWOT, exam trends, roadmap engine)
├── hitl/              # Human-in-the-loop feedback processing
├── analytics/         # Custom logging and metrics
├── data/              # Sample student data
├── Dockerfile         # HuggingFace Spaces deployment
└── requirements.txt
```
