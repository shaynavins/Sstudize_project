import json
from datetime import date, datetime
from langchain_core.tools import tool
from backend.database import SessionLocal
from backend.models import (
    StudentDB, PerformanceMetricDB, StudyTaskDB,
    FeedbackDB, RoadmapDB, WeeklyReportDB, SWOTAnalysisDB,
)
from core.exam_trends import get_exam_trends, get_priority_topics

###makes a normal python function into one that can be called by agent 

@tool
def query_student_data(student_id: int) -> str:
    """Fetch a student's full profile including name, grade, exam target, scores, subjects, strengths, and weaknesses."""
    db = SessionLocal()
    try:
        student = db.query(StudentDB).filter(StudentDB.id == student_id).first()
        if not student:
            return f"Error: Student with id {student_id} not found."
        return json.dumps({"id": student.id, "name": student.name, "grade": student.grade, "exam_target": student.exam_target, "target_score": student.target_score, "current_score": student.current_score, "study_hours_per_day": student.study_hours_per_day, "subjects": student.subjects, "strengths": student.strengths, "weaknesses": student.weaknesses})
    finally:
        db.close()


@tool
def get_performance_history(student_id: int) -> str:
    """Fetch all test scores and practice results for a student, ordered by date."""
    db = SessionLocal()
    try:
        metrics = db.query(PerformanceMetricDB).filter(PerformanceMetricDB.student_id == student_id).order_by(PerformanceMetricDB.date_taken.desc()).all()
        return json.dumps([{"subject": m.subject, "topic": m.topic, "score": m.score, "max_score": m.max_score, "test_type": m.test_type, "date_taken": str(m.date_taken), "time_spent_minutes": m.time_spent_minutes} for m in metrics])
    finally:
        db.close()


@tool
def get_task_completion_stats(student_id: int) -> str:
    """Get task completion statistics for a student including completed, pending, and overdue counts."""
    db = SessionLocal()
    try:
        tasks = db.query(StudyTaskDB).filter(StudyTaskDB.student_id == student_id).all()
        today = date.today()
        completed = [t for t in tasks if t.completed]
        pending = [t for t in tasks if not t.completed and t.scheduled_date >= today]
        overdue = [t for t in tasks if not t.completed and t.scheduled_date < today]
        subject_stats = {}
        for t in tasks:
            if t.subject not in subject_stats:
                subject_stats[t.subject] = {"total": 0, "completed": 0, "overdue": 0}
            subject_stats[t.subject]["total"] += 1
            if t.completed:
                subject_stats[t.subject]["completed"] += 1
            elif t.scheduled_date < today:
                subject_stats[t.subject]["overdue"] += 1
        skipped_by_type = {}
        for t in overdue:
            skipped_by_type[t.task_type] = skipped_by_type.get(t.task_type, 0) + 1
        total = len(tasks)
        adherence = (len(completed) / total * 100) if total > 0 else 0
        return json.dumps({"total_tasks": total, "completed": len(completed), "pending": len(pending), "overdue": len(overdue), "adherence_score": round(adherence, 1), "subject_breakdown": subject_stats, "skipped_by_task_type": skipped_by_type, "overdue_tasks": [{"subject": t.subject, "topic": t.topic, "description": t.description, "scheduled_date": str(t.scheduled_date), "priority": t.priority} for t in overdue]})
    finally:
        db.close()


@tool
def get_exam_trend_data(exam_type: str) -> str:
    """Get exam trend data including topic weightage, difficulty levels, and question frequency."""
    trends = get_exam_trends(exam_type)
    if not trends:
        return f"No exam trend data found for '{exam_type}'. Available: JEE Main, JEE Advanced, NEET"
    return json.dumps(trends, default=str)


@tool
def get_priority_topics_for_student(student_id: int) -> str:
    """Cross-reference exam trends with student scores to find the most urgent topics to focus on."""
    db = SessionLocal()
    try:
        student = db.query(StudentDB).filter(StudentDB.id == student_id).first()
        if not student:
            return f"Error: Student with id {student_id} not found."
        topics = get_priority_topics(student.exam_target, student.subjects)
        return json.dumps(topics[:15])
    finally:
        db.close()


@tool
def get_hitl_feedback(student_id: int) -> str:
    """Get all pending unresolved feedback from teachers and parents for a student."""
    db = SessionLocal()
    try:
        feedbacks = db.query(FeedbackDB).filter(FeedbackDB.student_id == student_id, FeedbackDB.resolved == False).order_by(FeedbackDB.created_at.desc()).all()
        return json.dumps([{"id": f.id, "source": f.source, "feedback_type": f.feedback_type, "content": f.content, "status": f.status, "created_at": str(f.created_at)} for f in feedbacks])
    finally:
        db.close()


@tool
def get_latest_swot(student_id: int) -> str:
    """Get the most recent SWOT analysis for a student."""
    db = SessionLocal()
    try:
        swot = db.query(SWOTAnalysisDB).filter(SWOTAnalysisDB.student_id == student_id).order_by(SWOTAnalysisDB.created_at.desc()).first()
        if not swot:
            return "No SWOT analysis found for this student."
        return json.dumps({"strengths": swot.strengths, "weaknesses": swot.weaknesses, "opportunities": swot.opportunities, "challenges": swot.challenges, "action_plan": swot.action_plan})
    finally:
        db.close()


@tool
def save_weekly_report(student_id: int, week_number: int, tasks_completed: int, tasks_pending: int, tasks_overdue: int, adherence_score: float, deviations: str, recommendations: str, agent_notes: str) -> str:
    """Save a weekly report generated by the review agent to the database."""
    db = SessionLocal()
    try:
        report = WeeklyReportDB(
            student_id=student_id, week_number=week_number, tasks_completed=tasks_completed,
            tasks_pending=tasks_pending, tasks_overdue=tasks_overdue, adherence_score=adherence_score,
            deviations=json.loads(deviations) if isinstance(deviations, str) else deviations,
            recommendations=json.loads(recommendations) if isinstance(recommendations, str) else recommendations,
            agent_notes=agent_notes,
        )
        db.add(report)
        db.commit()
        return f"Weekly report saved successfully (id={report.id})"
    except Exception as e:
        db.rollback()
        return f"Error saving report: {str(e)}"
    finally:
        db.close()


@tool
def send_notification(recipient_type: str, student_id: int, message: str) -> str:
    """Send a notification to a teacher or parent about a student."""
    db = SessionLocal()
    try:
        from backend.models import AnalyticsLogDB
        log = AnalyticsLogDB(event_type="notification", user_type=recipient_type, details={"student_id": student_id, "message": message, "recipient": recipient_type})
        db.add(log)
        db.commit()
        return f"Notification sent to {recipient_type} for student {student_id}: {message}"
    except Exception as e:
        db.rollback()
        return f"Error sending notification: {str(e)}"
    finally:
        db.close()


MONITORING_TOOLS = [query_student_data, get_task_completion_stats, get_performance_history]
REVIEW_TOOLS = [query_student_data, get_task_completion_stats, get_performance_history, get_hitl_feedback, save_weekly_report, send_notification]
ROADMAP_TOOLS = [query_student_data, get_performance_history, get_priority_topics_for_student, get_exam_trend_data, get_latest_swot, get_hitl_feedback]
