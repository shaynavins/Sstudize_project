from typing import List

CONFLICT_PATTERNS = [
    {"name": "workload_conflict", "teacher_signals": ["add_tasks", "increase_practice", "more_problems", "task_modification"], "parent_signals": ["reduce_load", "burnout", "high_stress", "health"], "description": "Teacher wants more work, parent flags overload"},
    {"name": "schedule_conflict", "teacher_signals": ["extend_hours", "weekend_study", "extra_sessions"], "parent_signals": ["change_schedule", "family_event", "add_break"], "description": "Teacher wants more time, parent wants flexibility"},
    {"name": "priority_conflict", "teacher_signals": ["focus_weak_areas", "change_subject_priority"], "parent_signals": ["reduce_load", "stress"], "description": "Teacher wants to shift focus, parent wants reduced pressure"},
]


def detect_and_resolve_conflicts(feedback_list: List[dict]) -> dict:
    teacher_feedback = [f for f in feedback_list if f["source"] == "teacher"]
    parent_feedback = [f for f in feedback_list if f["source"] == "parent"]
    if not teacher_feedback or not parent_feedback:
        return {"conflicts_found": 0, "conflicts": [], "resolution": "No conflicts, only one stakeholder has pending feedback"}

    teacher_signals = _extract_signals(teacher_feedback)
    parent_signals = _extract_signals(parent_feedback)
    detected = []
    for pattern in CONFLICT_PATTERNS:
        t_match = any(s in teacher_signals for s in pattern["teacher_signals"])
        p_match = any(s in parent_signals for s in pattern["parent_signals"])
        if t_match and p_match:
            resolution = _resolve_conflict(pattern["name"], teacher_feedback, parent_feedback)
            detected.append({
                "type": pattern["name"], "description": pattern["description"],
                "feedback_ids": [f["id"] for f in teacher_feedback + parent_feedback],
                "resolution": resolution["action"], "resolution_detail": resolution["detail"],
                "resolution_applied": True, "resolved_ids": resolution.get("resolved_ids", []),
            })
    return {"conflicts_found": len(detected), "conflicts": detected, "resolution": "All conflicts resolved" if detected else "No conflicts detected"}


def _extract_signals(feedback_list: List[dict]) -> set:
    signals = set()
    for fb in feedback_list:
        signals.add(fb.get("feedback_type", ""))
        content = fb.get("content", {})
        if isinstance(content, dict):
            if content.get("action") in ("reject", "modify"):
                signals.add("task_modification")
            if content.get("adjustment_type"):
                signals.add(content["adjustment_type"])
            if content.get("stress_level", 0) >= 4:
                signals.update(["high_stress", "burnout"])
            if content.get("health_issues"):
                signals.add("health")
            if content.get("recommended_focus_areas"):
                signals.update(["focus_weak_areas", "change_subject_priority"])
            if "more" in str(content).lower() or "increase" in str(content).lower():
                signals.update(["add_tasks", "increase_practice"])
    return signals


def _resolve_conflict(conflict_type, teacher_feedback, parent_feedback):
    teacher_ids = [f["id"] for f in teacher_feedback]
    parent_ids = [f["id"] for f in parent_feedback]
    if conflict_type == "workload_conflict":
        return {"action": "compromise", "detail": "Teacher focus areas preserved but total hours reduced for burnout concerns.", "resolved_ids": parent_ids}
    elif conflict_type == "schedule_conflict":
        return {"action": "parent_priority", "detail": "Parent schedule constraints take priority. Content redistributed.", "resolved_ids": parent_ids}
    elif conflict_type == "priority_conflict":
        return {"action": "teacher_priority_reduced_intensity", "detail": "Teacher focus areas adopted at 70% intensity.", "resolved_ids": teacher_ids}
    return {"action": "no_change", "detail": "Unknown conflict type", "resolved_ids": []}
