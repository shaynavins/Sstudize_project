from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    FeedbackDB, FeedbackCreate, FeedbackResponse,
    RoadmapDB, StudentDB,
)

router = APIRouter(prefix="/api/hitl", tags=["HITL"])


@router.post("/feedback", response_model=FeedbackResponse, status_code=201)
def submit_feedback(data: FeedbackCreate, db: Session = Depends(get_db)):
    student = db.query(StudentDB).filter(StudentDB.id == data.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if data.source not in ("teacher", "parent"):
        raise HTTPException(status_code=400, detail="Source must be teacher or parent")
    feedback = FeedbackDB(**data.model_dump())
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


@router.get("/feedback/{student_id}", response_model=List[FeedbackResponse])
def get_feedback(student_id: int, source: str = None, db: Session = Depends(get_db)):
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


@router.put("/roadmap/{roadmap_id}/reject")
def reject_roadmap(roadmap_id: int, db: Session = Depends(get_db)):
    roadmap = db.query(RoadmapDB).filter(RoadmapDB.id == roadmap_id).first()
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    roadmap.approved_by_teacher = False
    roadmap.status = "revised"
    db.commit()
    return {"status": "rejected", "roadmap_id": roadmap_id}


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
