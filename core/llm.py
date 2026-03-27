from openai import OpenAI
from langchain_openai import ChatOpenAI


def get_openai_client(api_key):
    return OpenAI(api_key=api_key)


def get_llm(api_key, model="gpt-4.1-mini", temperature=0.7):
    return ChatOpenAI(model=model, api_key=api_key, temperature=temperature)


def call_llm(api_key, system_prompt, user_prompt, model="gpt-4.1-mini", temperature=0.7):
    client = get_openai_client(api_key)
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content


SWOT_SYSTEM_PROMPT = """You are an expert academic counselor specializing in competitive exam preparation (JEE, NEET).

Analyze the student's performance data and generate a SWOT analysis.

You MUST respond with valid JSON in exactly this format:
{
  "strengths": [{"area": "topic name", "detail": "why this is a strength"}],
  "weaknesses": [{"area": "topic name", "detail": "why this is a weakness"}],
  "opportunities": [{"area": "topic name", "detail": "how the student can improve here"}],
  "challenges": [{"area": "topic name", "detail": "what makes this difficult"}],
  "action_plan": [{"action": "specific recommendation", "priority": "high/medium/low"}]
}

Be specific. Reference actual scores and topics from the data. Give 3-5 items per category.
The action plan should have 5-7 concrete, actionable steps."""

ROADMAP_SYSTEM_PROMPT = """You are an expert study planner for competitive exam preparation (JEE, NEET).

Create a personalized weekly study roadmap based on the student's profile, SWOT analysis, exam trends, and any teacher/parent feedback.

You MUST respond with valid JSON in exactly this format:
{
  "goals": ["goal 1", "goal 2", "goal 3"],
  "tasks": [
    {
      "subject": "Physics",
      "topic": "Thermodynamics",
      "description": "Specific task description",
      "task_type": "study/practice/revision/test",
      "priority": "high/medium/low",
      "estimated_hours": 1.5,
      "day": "Monday",
      "resources": [{"type": "video/book/pdf", "title": "Resource name", "url": ""}]
    }
  ],
  "time_allocation": {"Physics": 10, "Chemistry": 8, "Mathematics": 12},
  "weekly_hours_total": 30,
  "notes": "Any additional recommendations"
}

Rules:
- Prioritize weak areas (more time on low-scoring topics)
- Balance study, practice, and revision tasks
- Include specific resources where possible
- Respect the student's available study hours per day
- Generate tasks for 7 days (Monday through Sunday)
- Each day should have 2-4 tasks"""
