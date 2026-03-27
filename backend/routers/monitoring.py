from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import require_api_key
from backend.models import WeeklyReportDB, WeeklyReportResponse
from agents.orchestrator import run_single_agent, run_full_pipeline

router = APIRouter(prefix="/api/monitoring", tags=["Monitoring"])


@router.post("/run/{student_id}")
def run_monitoring_agent(student_id: int, api_key: str = Depends(require_api_key)):
    result = run_single_agent("monitoring", student_id, api_key)
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.post("/review/{student_id}")
def run_review_agent(student_id: int, api_key: str = Depends(require_api_key)):
    result = run_single_agent("review", student_id, api_key)
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.post("/pipeline/{student_id}")
def run_agent_pipeline(student_id: int, api_key: str = Depends(require_api_key)):
    return run_full_pipeline(student_id, api_key)


@router.get("/reports/{student_id}", response_model=List[WeeklyReportResponse])
def get_reports(student_id: int, db: Session = Depends(get_db)):
    return (
        db.query(WeeklyReportDB)
        .filter(WeeklyReportDB.student_id == student_id)
        .order_by(WeeklyReportDB.created_at.desc())
        .all()
    )


@router.get("/reports/{student_id}/latest", response_model=WeeklyReportResponse)
def get_latest_report(student_id: int, db: Session = Depends(get_db)):
    report = (
        db.query(WeeklyReportDB)
        .filter(WeeklyReportDB.student_id == student_id)
        .order_by(WeeklyReportDB.created_at.desc())
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="No reports found")
    return report
