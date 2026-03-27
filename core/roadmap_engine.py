from __future__ import annotations

import json
from datetime import date, timedelta
from core.llm import call_llm, ROADMAP_SYSTEM_PROMPT
from core.exam_trends import get_exam_trends, get_priority_topics


def generate_roadmap(student_data, swot_data, feedback_list, api_key, week_start=None):
    if week_start is None:
        today = date.today()
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        week_start = today + timedelta(days=days_until_monday)
    week_end = week_start + timedelta(days=6)

    exam_type = student_data.get("exam_target", "JEE Main")
    priority_topics = get_priority_topics(exam_type, student_data.get("subjects", {}))

    user_message = f"""Create a weekly study roadmap for this student:

Student Profile:
- Name: {student_data.get('name')}
- Grade: {student_data.get('grade')}
- Exam Target: {exam_type}
- Target Score: {student_data.get('target_score')}
- Current Score: {student_data.get('current_score')}
- Study Hours/Day: {student_data.get('study_hours_per_day')}
- Subjects: {json.dumps(student_data.get('subjects', {}))}
- Strengths: {student_data.get('strengths', [])}
- Weaknesses: {student_data.get('weaknesses', [])}

Week: {week_start} to {week_end}
Weekly capacity: {student_data.get('study_hours_per_day', 6) * 7} hours
"""
    if swot_data:
        user_message += f"""
SWOT Analysis:
- Strengths: {json.dumps(swot_data.get('strengths', []))}
- Weaknesses: {json.dumps(swot_data.get('weaknesses', []))}
- Opportunities: {json.dumps(swot_data.get('opportunities', []))}
- Action Plan: {json.dumps(swot_data.get('action_plan', []))}
"""
    if priority_topics:
        user_message += "\nHigh-Priority Topics:\n"
        for pt in priority_topics[:10]:
            user_message += f"- {pt['subject']}/{pt['topic']}: urgency={pt['urgency_score']}, weightage={pt['weightage']}%\n"
    if feedback_list:
        user_message += "\nPending Feedback:\n"
        for fb in feedback_list:
            user_message += f"- [{fb.get('source', 'unknown').upper()}] ({fb.get('feedback_type', '')}): {json.dumps(fb.get('content', {}))}\n"

    user_message += "\nGenerate the weekly roadmap now."
    raw = call_llm(api_key, ROADMAP_SYSTEM_PROMPT, user_message)

    try:
        content = raw.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            content = content.rsplit("```", 1)[0]
        result = json.loads(content)
        result["week_start"] = str(week_start)
        result["week_end"] = str(week_end)
        result["exam_type"] = exam_type
        return result
    except json.JSONDecodeError:
        return {"goals": ["Error generating roadmap"], "tasks": [], "time_allocation": {}, "weekly_hours_total": 0, "notes": "Failed to parse LLM response", "_raw_response": raw}
