from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    StudentDB, StudyTaskDB, PerformanceMetricDB,
    FeedbackDB, WeeklyReportDB, AnalyticsLogDB,
)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/{student_id}")
def get_student_dashboard(student_id: int, db: Session = Depends(get_db)):
    student = db.query(StudentDB).filter(StudentDB.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    tasks = db.query(StudyTaskDB).filter(StudyTaskDB.student_id == student_id).all()
    today = date.today()
    completed = sum(1 for t in tasks if t.completed)
    overdue = sum(1 for t in tasks if not t.completed and t.scheduled_date < today)
    total = len(tasks)

    subject_scores = {}
    metrics = (
        db.query(PerformanceMetricDB)
        .filter(PerformanceMetricDB.student_id == student_id)
        .order_by(PerformanceMetricDB.date_taken.desc())
        .all()
    )
    for m in metrics:
        key = f"{m.subject}/{m.topic}"
        if key not in subject_scores:
            subject_scores[key] = {"subject": m.subject, "topic": m.topic, "score": m.score, "date": str(m.date_taken)}

    latest_report = (
        db.query(WeeklyReportDB)
        .filter(WeeklyReportDB.student_id == student_id)
        .order_by(WeeklyReportDB.created_at.desc())
        .first()
    )

    pending_feedback = (
        db.query(FeedbackDB)
        .filter(FeedbackDB.student_id == student_id, FeedbackDB.resolved == False)
        .count()
    )

    return {
        "student": {
            "id": student.id, "name": student.name, "grade": student.grade,
            "exam_target": student.exam_target, "target_score": student.target_score,
            "current_score": student.current_score,
        },
        "task_summary": {
            "total": total, "completed": completed, "overdue": overdue,
            "pending": total - completed - overdue,
            "adherence_percent": round(completed / total * 100, 1) if total > 0 else 0,
        },
        "recent_scores": list(subject_scores.values())[:10],
        "latest_report": {
            "adherence_score": latest_report.adherence_score if latest_report else None,
            "recommendations": latest_report.recommendations if latest_report else [],
            "agent_notes": latest_report.agent_notes if latest_report else None,
            "created_at": str(latest_report.created_at) if latest_report else None,
        },
        "pending_feedback_count": pending_feedback,
    }


@router.get("/analytics/summary")
def get_analytics_summary(db: Session = Depends(get_db)):
    total_students = db.query(StudentDB).count()
    total_tasks = db.query(StudyTaskDB).count()
    completed_tasks = db.query(StudyTaskDB).filter(StudyTaskDB.completed == True).count()
    total_feedback = db.query(FeedbackDB).count()
    total_reports = db.query(WeeklyReportDB).count()
    agent_invocations = db.query(AnalyticsLogDB).filter(AnalyticsLogDB.event_type == "agent_invocation").count()

    return {
        "total_students": total_students,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "task_completion_rate": round(completed_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0,
        "total_feedback_items": total_feedback,
        "total_weekly_reports": total_reports,
        "agent_invocations": agent_invocations,
    }
