from langgraph.prebuilt import create_react_agent
from agents.tools import MONITORING_TOOLS
from core.llm import get_llm

MONITORING_PROMPT = """You are a Progress Monitoring Agent for a student study system.

Your role: Analyze a student's task completion and performance data to identify deviations from their study roadmap.

Your process:
1. Query the student's profile to understand their context
2. Get their task completion statistics to see adherence
3. Get their performance history to identify score trends
4. Analyze: Are certain subjects being neglected? Are revision tasks being skipped?
5. Rate each deviation by severity (info/warning/critical)
6. Decide if this needs teacher escalation

Provide your final analysis as JSON:
{
    "student_name": "...",
    "adherence_score": 75.0,
    "deviations": [
        {"type": "skipped", "severity": "warning", "detail": "...", "subject": "...", "topic": "..."}
    ],
    "insights": "Overall analysis paragraph",
    "should_escalate": true,
    "escalation_reason": "reason or null"
}"""


def create_monitoring_agent(api_key):
    llm = get_llm(api_key, temperature=0.3)
    return create_react_agent(llm, tools=MONITORING_TOOLS, prompt=MONITORING_PROMPT)


def run_monitoring(student_id, api_key):
    graph = create_monitoring_agent(api_key)
    result = graph.invoke({
        "messages": [("user", f"Analyze the progress of student with ID {student_id}")]
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
