

def process_roadmap_review(feedback_content: dict) -> dict:
 action = feedback_content.get("action", "approve")
 modifications = feedback_content.get("task_modifications", [])

 return {
 "processed": True,
 "action": action,
 "modification_count": len(modifications),
 "requires_regeneration": action == "reject",
 "notes": feedback_content.get("notes", ""),
 }


def process_weekly_assessment(feedback_content: dict) -> dict:
 concerns = feedback_content.get("non_academic_concerns")
 focus_areas = feedback_content.get("recommended_focus_areas", [])

 return {
 "processed": True,
 "has_concerns": concerns is not None and len(str(concerns)) > 0,
 "focus_area_count": len(focus_areas),
 "priority": "high" if concerns else "medium",
 }
