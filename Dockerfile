FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x start.sh

# HuggingFace Spaces serves on port 8501 (Streamlit)
# FastAPI runs internally on port 7860
EXPOSE 8501

ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_HOME=/tmp/.streamlit

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

CMD ["bash", "start.sh"]
