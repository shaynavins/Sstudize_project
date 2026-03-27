from langgraph.prebuilt import create_react_agent
from agents.tools import REVIEW_TOOLS
from core.llm import get_llm

REVIEW_PROMPT = """You are a Weekly Review Agent for a student study system.

Your role: Synthesize a student's weekly data into a comprehensive report with actionable recommendations.

Your process:
1. Query the student's profile to understand context
2. Get task completion statistics for adherence data
3. Get performance history to see score trends
4. Check for any pending feedback from teachers/parents
5. Synthesize everything into a weekly report
6. Decide whether to notify teacher and/or parent
7. Save the report using the save_weekly_report tool
8. If needed, send notifications using the send_notification tool

Your report should highlight what went well, flag areas of concern, and give specific actionable recommendations.

After analysis, save the report using the save_weekly_report tool, then provide your final summary as JSON:
{
    "summary": "2-3 sentence overview",
    "adherence_score": 75.0,
    "key_achievements": ["..."],
    "areas_of_concern": ["..."],
    "recommendations": [{"action": "...", "reason": "...", "priority": "high/medium/low"}],
    "notified_teacher": true,
    "notified_parent": false
}"""


def create_review_agent(api_key):
    llm = get_llm(api_key, temperature=0.4)
    return create_react_agent(llm, tools=REVIEW_TOOLS, prompt=REVIEW_PROMPT)


def run_review(student_id, api_key, prior_context=""):
    graph = create_review_agent(api_key)
    user_msg = f"Generate a weekly review report for student with ID {student_id}"
    if prior_context:
        user_msg += f"\n\nThe Monitoring Agent has already analyzed this student and found:\n{prior_context}\n\nUse these findings as input for your review. Do NOT re-analyze from scratch."
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
