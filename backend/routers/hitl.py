from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import require_api_key
from backend.models import (
    FeedbackDB, FeedbackCreate, FeedbackResponse,
    RoadmapDB, StudentDB, StudyTaskDB,
)

router = APIRouter(prefix="/api/hitl", tags=["HITL"])



@router.post("/feedback", response_model=FeedbackResponse, status_code=201)
def submit_feedback(data: FeedbackCreate, db: Session = Depends(get_db)):
    """Submit teacher or parent feedback. Runs through the relevant HITL processor."""
    student = db.query(StudentDB).filter(StudentDB.id == data.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if data.source not in ("teacher", "parent"):
        raise HTTPException(status_code=400, detail="Source must be teacher or parent")

    processing_result = {}
    if data.source == "teacher":
        from hitl.teacher import process_roadmap_review, process_weekly_assessment
        if data.feedback_type in ("roadmap_review", "task_modification"):
            processing_result = process_roadmap_review(data.content)
        else:
            processing_result = process_weekly_assessment(data.content)
    elif data.source == "parent":
        from hitl.parent import process_observation, process_goal_adjustment
        if data.feedback_type == "goal_adjustment":
            processing_result = process_goal_adjustment(data.content)
        else:
            processing_result = process_observation(data.content)

    content_with_meta = data.content.copy() if isinstance(data.content, dict) else data.content
    if isinstance(content_with_meta, dict):
        content_with_meta["_processing"] = processing_result

    feedback = FeedbackDB(
        student_id=data.student_id,
        source=data.source,
        feedback_type=data.feedback_type,
        content=content_with_meta,
        status="urgent" if processing_result.get("priority") == "high" else "pending",
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


@router.get("/feedback/{student_id}", response_model=List[FeedbackResponse])
def get_feedback(student_id: int, source: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(FeedbackDB).filter(FeedbackDB.student_id == student_id)
    if source:
        query = query.filter(FeedbackDB.source == source)
    return query.order_by(FeedbackDB.created_at.desc()).all()


@router.get("/feedback/{student_id}/pending", response_model=List[FeedbackResponse])
def get_pending_feedback(student_id: int, db: Session = Depends(get_db)):
    return (
        db.query(FeedbackDB)
        .filter(FeedbackDB.student_id == student_id, FeedbackDB.resolved == False)
        .order_by(FeedbackDB.created_at.desc())
        .all()
    )


@router.put("/feedback/{feedback_id}/resolve")
def resolve_feedback(feedback_id: int, db: Session = Depends(get_db)):
    feedback = db.query(FeedbackDB).filter(FeedbackDB.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    feedback.resolved = True
    feedback.status = "applied"
    db.commit()
    return {"status": "resolved", "feedback_id": feedback_id}


@router.put("/feedback/{feedback_id}/reject")
def reject_feedback(feedback_id: int, db: Session = Depends(get_db)):
    feedback = db.query(FeedbackDB).filter(FeedbackDB.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    feedback.resolved = True
    feedback.status = "rejected"
    db.commit()
    return {"status": "rejected", "feedback_id": feedback_id}



@router.put("/roadmap/{roadmap_id}/approve")
def approve_roadmap(roadmap_id: int, db: Session = Depends(get_db)):
    roadmap = db.query(RoadmapDB).filter(RoadmapDB.id == roadmap_id).first()
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    roadmap.approved_by_teacher = True
    db.commit()
    return {"status": "approved", "roadmap_id": roadmap_id}


class RoadmapRejectRequest(BaseModel):
    reason: str = ""
    auto_regenerate: bool = False


@router.put("/roadmap/{roadmap_id}/reject")
def reject_roadmap(
    roadmap_id: int,
    body: Optional[RoadmapRejectRequest] = None,
    db: Session = Depends(get_db),
    api_key: Optional[str] = Depends(require_api_key),
):
    """Reject a roadmap. Optionally store rejection reason and trigger regeneration."""
    roadmap = db.query(RoadmapDB).filter(RoadmapDB.id == roadmap_id).first()
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    roadmap.approved_by_teacher = False
    roadmap.status = "rejected"
    db.commit()

    result = {"status": "rejected", "roadmap_id": roadmap_id}

    if body and body.reason:
        rejection_fb = FeedbackDB(
            student_id=roadmap.student_id,
            source="teacher",
            feedback_type="roadmap_review",
            content={"action": "reject", "notes": body.reason},
            status="pending",
        )
        db.add(rejection_fb)
        db.commit()

    if body and body.auto_regenerate and api_key:
        from backend.routers.roadmap import _collect_student_context, _save_roadmap_and_tasks
        from core.roadmap_engine import generate_roadmap
        student, student_data, swot_data, feedback_list = _collect_student_context(db, roadmap.student_id)
        if student:
            new_result = generate_roadmap(student_data, swot_data, feedback_list, api_key)
            _save_roadmap_and_tasks(db, roadmap.student_id, new_result)
            db.query(FeedbackDB).filter(
                FeedbackDB.student_id == roadmap.student_id, FeedbackDB.resolved == False,
            ).update({"resolved": True, "status": "applied"}, synchronize_session="fetch")
            db.commit()
            result["regenerated"] = True
            result["new_roadmap"] = new_result

    return result



class TaskReviewRequest(BaseModel):
    action: str  
    modification_notes: str = ""
    new_priority: Optional[str] = None
    new_estimated_hours: Optional[float] = None


@router.put("/task/{task_id}/review")
def review_task(task_id: int, body: TaskReviewRequest, db: Session = Depends(get_db)):
    """Teacher reviews individual tasks: approve, modify, or remove."""
    task = db.query(StudyTaskDB).filter(StudyTaskDB.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if body.action == "remove":
        db.delete(task)
        db.commit()
        return {"status": "removed", "task_id": task_id}

    if body.action == "modify":
        if body.new_priority:
            task.priority = body.new_priority
        if body.new_estimated_hours is not None:
            task.estimated_hours = body.new_estimated_hours
        if body.modification_notes:
            task.description = f"{task.description} [Teacher: {body.modification_notes}]"
        db.commit()
        return {"status": "modified", "task_id": task_id}

    return {"status": "approved", "task_id": task_id}



@router.post("/resolve-conflicts/{student_id}")
def resolve_conflicts(student_id: int, db: Session = Depends(get_db)):
    from hitl.conflict_resolver import detect_and_resolve_conflicts
    pending = (
        db.query(FeedbackDB)
        .filter(FeedbackDB.student_id == student_id, FeedbackDB.resolved == False)
        .all()
    )
    feedback_list = [
        {"id": f.id, "source": f.source, "feedback_type": f.feedback_type, "content": f.content}
        for f in pending
    ]
    result = detect_and_resolve_conflicts(feedback_list)
    for conflict in result.get("conflicts", []):
        for fid in conflict.get("feedback_ids", []):
            fb = db.query(FeedbackDB).filter(FeedbackDB.id == fid).first()
            if fb:
                fb.status = "conflict"
        if conflict.get("resolution_applied"):
            for fid in conflict.get("resolved_ids", []):
                fb = db.query(FeedbackDB).filter(FeedbackDB.id == fid).first()
                if fb:
                    fb.resolved = True
                    fb.status = "applied"
    db.commit()
    return result
