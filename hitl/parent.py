def process_observation(feedback_content):
    stress = feedback_content.get("stress_level", 3)
    health = feedback_content.get("health_issues")
    priority = "low"
    if stress >= 4 or health:
        priority = "high"
    elif stress >= 3:
        priority = "medium"
    flags = []
    if stress >= 4:
        flags.append("high_stress")
    if health:
        flags.append("health_concern")
    if feedback_content.get("study_pattern") == "declining":
        flags.append("declining_pattern")
    if feedback_content.get("sleep_hours", 7) < 6:
        flags.append("sleep_deficit")
    return {"processed": True, "priority": priority, "flags": flags, "recommend_load_reduction": stress >= 4}


def process_goal_adjustment(feedback_content):
    adj_type = feedback_content.get("adjustment_type", "reduce_load")
    reason = feedback_content.get("reason", "")
    return {
        "processed": True, "adjustment_type": adj_type, "reason": reason,
        "duration_days": feedback_content.get("duration_days", 7),
        "affects_all_subjects": feedback_content.get("affected_subjects") is None,
        "priority": "high" if reason in ("health", "burnout") else "medium",
    }
