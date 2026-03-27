import json
from core.llm import call_llm, SWOT_SYSTEM_PROMPT


def generate_swot(student_data, metrics_data, api_key):
    user_message = f"""Analyze this student and generate a SWOT analysis:

Student Profile:
- Name: {student_data.get('name')}
- Grade: {student_data.get('grade')}
- Exam Target: {student_data.get('exam_target')}
- Target Score: {student_data.get('target_score')}
- Current Score: {student_data.get('current_score')}
- Study Hours/Day: {student_data.get('study_hours_per_day')}
- Subjects: {json.dumps(student_data.get('subjects', {}))}
- Strengths: {student_data.get('strengths', [])}
- Weaknesses: {student_data.get('weaknesses', [])}

Performance History ({len(metrics_data)} records):
"""
    for m in metrics_data:
        user_message += f"- {m.get('subject')}/{m.get('topic')}: {m.get('score')}% ({m.get('test_type')}, {m.get('date_taken')})\n"

    raw = call_llm(api_key, SWOT_SYSTEM_PROMPT, user_message)

    try:
        content = raw.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            content = content.rsplit("```", 1)[0]
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "strengths": [{"area": "Parse Error", "detail": "Could not parse LLM response"}],
            "weaknesses": [], "opportunities": [], "challenges": [], "action_plan": [],
            "_raw_response": raw,
        }
