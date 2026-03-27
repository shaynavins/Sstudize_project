from langgraph.prebuilt import create_react_agent
from agents.tools import ROADMAP_TOOLS
from core.llm import get_llm

ROADMAP_PROMPT = """You are a Study Roadmap Planning Agent for competitive exam preparation.

Your role: Create an optimal personalized weekly study plan for a student.

Your process:
1. Query the student's profile (subjects, scores, target, study hours)
2. Get their performance history to understand trends
3. Get their SWOT analysis (if available)
4. Get priority topics based on exam trends and student weaknesses
5. Check for pending teacher/parent feedback - this MUST influence your plan
6. Reason about tradeoffs: weak areas need more time, but don't neglect strengths
7. Generate a structured weekly roadmap

Rules:
- Prioritize high-urgency topics (high exam weightage + low student score)
- Balance study, practice, and revision tasks
- Respect the student's available study hours per day
- If teacher feedback says "add more practice", do it
- If parent feedback flags burnout, reduce load
- Each day should have 2-4 tasks

Provide your final answer as JSON:
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
            "resources": [{"type": "video/book/pdf", "title": "...", "url": ""}]
        }
    ],
    "time_allocation": {"Physics": 10, "Chemistry": 8},
    "weekly_hours_total": 30,
    "notes": "Additional recommendations"
}"""


def create_roadmap_agent(api_key):
    llm = get_llm(api_key, temperature=0.5)
    return create_react_agent(llm, tools=ROADMAP_TOOLS, prompt=ROADMAP_PROMPT)


def run_roadmap_generation(student_id, api_key, prior_context=""):
    graph = create_roadmap_agent(api_key)
    user_msg = f"Generate a personalized weekly study roadmap for student with ID {student_id}"
    if prior_context:
        user_msg += f"\n\nPrior analysis from the Monitoring and Review agents:\n{prior_context}\n\nIncorporate these findings into your roadmap. Prioritize the issues flagged above."
    result = graph.invoke({
        "messages": [("user", user_msg)]
    })

    messages = result.get("messages", [])
    final_message = messages[-1].content if messages else ""

    steps = []
    for msg in messages:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                steps.append({"action": tc.get("name", ""), "input": str(tc.get("args", {})), "output": ""})
        if hasattr(msg, "name") and msg.name and steps:
            steps[-1]["output"] = str(msg.content)[:500]

    return {"output": final_message, "steps": steps}
