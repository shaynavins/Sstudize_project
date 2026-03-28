from typing import List
from datetime import date, timedelta, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import require_api_key
from backend.models import (
    StudentDB, PerformanceMetricDB, StudyTaskDB, RoadmapDB,
    SWOTAnalysisDB, FeedbackDB, StudyTaskResponse, RoadmapResponse, SWOTResponse,
)
from core.swot import generate_swot
from core.roadmap_engine import generate_roadmap

router = APIRouter(prefix="/api/roadmap", tags=["Roadmap"])



def _archive_old_roadmap_tasks(db: Session, student_id: int):
    """Mark previous active roadmaps as replaced and delete their incomplete tasks."""
    old_roadmaps = (
        db.query(RoadmapDB)
        .filter(RoadmapDB.student_id == student_id, RoadmapDB.status == "active")
        .all()
    )
    for rm in old_roadmaps:
        rm.status = "replaced"
        db.query(StudyTaskDB).filter(
            StudyTaskDB.roadmap_id == rm.id,
            StudyTaskDB.completed == False,
        ).delete(synchronize_session="fetch")


def _collect_student_context(db: Session, student_id: int):
    """Gather student profile, SWOT, and unresolved feedback in one place."""
    student = db.query(StudentDB).filter(StudentDB.id == student_id).first()
    if not student:
        return None, None, None, []
    student_data = {
        "name": student.name, "grade": student.grade, "exam_target": student.exam_target,
        "target_score": student.target_score, "current_score": student.current_score,
        "study_hours_per_day": student.study_hours_per_day, "subjects": student.subjects,
        "strengths": student.strengths, "weaknesses": student.weaknesses,
    }
    swot = (
        db.query(SWOTAnalysisDB)
        .filter(SWOTAnalysisDB.student_id == student_id)
        .order_by(SWOTAnalysisDB.created_at.desc())
        .first()
    )
    swot_data = None
    if swot:
        swot_data = {
            "strengths": swot.strengths, "weaknesses": swot.weaknesses,
            "opportunities": swot.opportunities, "action_plan": swot.action_plan,
        }
    feedbacks = (
        db.query(FeedbackDB)
        .filter(FeedbackDB.student_id == student_id, FeedbackDB.resolved == False)
        .all()
    )
    feedback_list = [
        {"source": f.source, "feedback_type": f.feedback_type, "content": f.content}
        for f in feedbacks
    ]
    return student, student_data, swot_data, feedback_list


def _parse_date(value, fallback: date) -> date:
    """Convert a string like '2026-03-30' to a Python date, or return the fallback."""
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except (ValueError, TypeError):
            pass
    return fallback


def _save_roadmap_and_tasks(db: Session, student_id: int, result: dict):
    """Persist a generated roadmap and its tasks, archiving old ones first."""
    _archive_old_roadmap_tasks(db, student_id)
    today = date.today()
    start = _parse_date(result.get("week_start"), today)
    end = _parse_date(result.get("week_end"), today + timedelta(days=6))
    roadmap_db = RoadmapDB(
        student_id=student_id,
        week_number=today.isocalendar()[1],
        start_date=start,
        end_date=end,
        goals=result.get("goals", []),
        status="active",
        ai_generated=True,
    )
    db.add(roadmap_db)
    db.flush()
    for task in result.get("tasks", []):
        task_db = StudyTaskDB(
            student_id=student_id, roadmap_id=roadmap_db.id,
            subject=task.get("subject", ""), topic=task.get("topic", ""),
            description=task.get("description", ""),
            task_type=task.get("task_type", "study"),
            priority=task.get("priority", "medium"),
            estimated_hours=task.get("estimated_hours", 1.0),
            scheduled_date=today,
            resources=task.get("resources", []),
        )
        db.add(task_db)
    db.commit()
    return roadmap_db



@router.post("/swot/{student_id}", response_model=SWOTResponse)
def generate_swot_analysis(student_id: int, db: Session = Depends(get_db), api_key: str = Depends(require_api_key)):
    student = db.query(StudentDB).filter(StudentDB.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    metrics = db.query(PerformanceMetricDB).filter(PerformanceMetricDB.student_id == student_id).all()
    student_data = {
        "name": student.name, "grade": student.grade, "exam_target": student.exam_target,
        "target_score": student.target_score, "current_score": student.current_score,
        "study_hours_per_day": student.study_hours_per_day, "subjects": student.subjects,
        "strengths": student.strengths, "weaknesses": student.weaknesses,
    }
    metrics_data = [
        {"subject": m.subject, "topic": m.topic, "score": m.score, "test_type": m.test_type, "date_taken": str(m.date_taken)}
        for m in metrics
    ]
    swot_result = generate_swot(student_data, metrics_data, api_key)
    swot_db = SWOTAnalysisDB(
        student_id=student_id,
        strengths=swot_result.get("strengths", []),
        weaknesses=swot_result.get("weaknesses", []),
        opportunities=swot_result.get("opportunities", []),
        challenges=swot_result.get("challenges", []),
        action_plan=swot_result.get("action_plan", []),
    )
    db.add(swot_db)
    db.commit()
    db.refresh(swot_db)
    return swot_db


@router.get("/swot/{student_id}", response_model=SWOTResponse)
def get_latest_swot(student_id: int, db: Session = Depends(get_db)):
    swot = db.query(SWOTAnalysisDB).filter(SWOTAnalysisDB.student_id == student_id).order_by(SWOTAnalysisDB.created_at.desc()).first()
    if not swot:
        raise HTTPException(status_code=404, detail="No SWOT analysis found")
    return swot



@router.post("/generate/{student_id}")
def generate_roadmap_direct(student_id: int, db: Session = Depends(get_db), api_key: str = Depends(require_api_key)):
    """Generate a new roadmap. Old active roadmap is archived and its incomplete tasks removed."""
    student, student_data, swot_data, feedback_list = _collect_student_context(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    result = generate_roadmap(student_data, swot_data, feedback_list, api_key)
    _save_roadmap_and_tasks(db, student_id, result)
    db.query(FeedbackDB).filter(
        FeedbackDB.student_id == student_id, FeedbackDB.resolved == False,
    ).update({"resolved": True, "status": "applied"}, synchronize_session="fetch")
    db.commit()
    return result


@router.post("/regenerate/{student_id}")
def regenerate_roadmap_with_feedback(student_id: int, db: Session = Depends(get_db), api_key: str = Depends(require_api_key)):
    """Run conflict resolution on pending feedback, then regenerate the roadmap."""
    from hitl.conflict_resolver import detect_and_resolve_conflicts

    pending = (
        db.query(FeedbackDB)
        .filter(FeedbackDB.student_id == student_id, FeedbackDB.resolved == False)
        .all()
    )
    feedback_dicts = [
        {"id": f.id, "source": f.source, "feedback_type": f.feedback_type, "content": f.content}
        for f in pending
    ]
    conflict_result = detect_and_resolve_conflicts(feedback_dicts)

    for conflict in conflict_result.get("conflicts", []):
        if conflict.get("resolution_applied"):
            for fid in conflict.get("resolved_ids", []):
                fb = db.query(FeedbackDB).filter(FeedbackDB.id == fid).first()
                if fb:
                    fb.resolved = True
                    fb.status = "applied"
    db.commit()

    student, student_data, swot_data, feedback_list = _collect_student_context(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    result = generate_roadmap(student_data, swot_data, feedback_list, api_key)
    _save_roadmap_and_tasks(db, student_id, result)

    db.query(FeedbackDB).filter(
        FeedbackDB.student_id == student_id, FeedbackDB.resolved == False,
    ).update({"resolved": True, "status": "applied"}, synchronize_session="fetch")
    db.commit()

    return {"roadmap": result, "conflicts": conflict_result}


@router.post("/agent-generate/{student_id}")
def generate_roadmap_agent(student_id: int, db: Session = Depends(get_db), api_key: str = Depends(require_api_key)):
    """Run the LangGraph roadmap agent, then parse and persist its output."""
    from agents.orchestrator import run_single_agent
    result = run_single_agent("roadmap", student_id, api_key)
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("error"))

  
    import json as _json
    output_text = result.get("output", "")
    try:
        content = output_text.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            content = content.rsplit("```", 1)[0]
        parsed = _json.loads(content)
        if isinstance(parsed, dict) and "tasks" in parsed:
            _save_roadmap_and_tasks(db, student_id, parsed)
            db.query(FeedbackDB).filter(
                FeedbackDB.student_id == student_id, FeedbackDB.resolved == False,
            ).update({"resolved": True, "status": "applied"}, synchronize_session="fetch")
            db.commit()
            result["saved_to_db"] = True
    except (_json.JSONDecodeError, Exception):
        result["saved_to_db"] = False

    return result



@router.get("/tasks/{student_id}", response_model=List[StudyTaskResponse])
def get_student_tasks(student_id: int, db: Session = Depends(get_db)):
    """Return only tasks belonging to the current active roadmap (+ completed from older ones)."""
    active_roadmap = (
        db.query(RoadmapDB)
        .filter(RoadmapDB.student_id == student_id, RoadmapDB.status == "active")
        .order_by(RoadmapDB.created_at.desc())
        .first()
    )
    if active_roadmap:
        return (
            db.query(StudyTaskDB)
            .filter(
                StudyTaskDB.student_id == student_id,
                (StudyTaskDB.roadmap_id == active_roadmap.id) | (StudyTaskDB.completed == True),
            )
            .order_by(StudyTaskDB.scheduled_date.asc())
            .all()
        )
    return db.query(StudyTaskDB).filter(StudyTaskDB.student_id == student_id).order_by(StudyTaskDB.scheduled_date.asc()).all()


@router.put("/tasks/{task_id}/complete")
def complete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(StudyTaskDB).filter(StudyTaskDB.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.completed = True
    task.completed_at = datetime.utcnow()
    db.commit()
    return {"status": "completed", "task_id": task_id}


@router.put("/tasks/{task_id}/uncomplete")
def uncomplete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(StudyTaskDB).filter(StudyTaskDB.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.completed = False
    task.completed_at = None
    db.commit()
    return {"status": "uncompleted", "task_id": task_id}


@router.get("/{student_id}", response_model=List[RoadmapResponse])
def get_roadmaps(student_id: int, db: Session = Depends(get_db)):
    return db.query(RoadmapDB).filter(RoadmapDB.student_id == student_id).order_by(RoadmapDB.created_at.desc()).all()
