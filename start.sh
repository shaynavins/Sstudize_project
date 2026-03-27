#!/bin/bash
# Start both FastAPI and Streamlit
# Used by Dockerfile for HuggingFace Spaces deployment

# Start FastAPI in background
uvicorn backend.main:app --host 0.0.0.0 --port 7860 &

# Wait for backend to start
sleep 3

# Start Streamlit in foreground
streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0
