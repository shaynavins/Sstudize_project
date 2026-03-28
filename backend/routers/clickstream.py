from typing import List, Optional
from datetime import datetime, timedelta
from collections import Counter

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.models import AnalyticsLogDB

router = APIRouter(prefix="/api/clickstream", tags=["Clickstream"])


class ClickstreamEvent(BaseModel):
    event_type: str          # page_view, button_click, form_submit, feature_use
    page: str                # e.g. "Roadmap", "Teacher Portal"
    action: Optional[str] = None   # e.g. "generate_roadmap", "approve_task"
    user_role: str = "student"
    student_id: Optional[int] = None
    session_id: Optional[str] = None
    metadata: Optional[dict] = None


class ClickstreamBatch(BaseModel):
    events: List[ClickstreamEvent]


# --------------- Event ingestion ---------------

@router.post("/track")
def track_event(event: ClickstreamEvent, db: Session = Depends(get_db)):
    """Record a single clickstream event."""
    log = AnalyticsLogDB(
        event_type=f"clickstream_{event.event_type}",
        user_type=event.user_role,
        details={
            "page": event.page,
            "action": event.action,
            "student_id": event.student_id,
            "session_id": event.session_id,
            **(event.metadata or {}),
        },
    )
    db.add(log)
    db.commit()
    return {"status": "tracked"}


@router.post("/track/batch")
def track_batch(batch: ClickstreamBatch, db: Session = Depends(get_db)):
    """Record multiple clickstream events at once."""
    for event in batch.events:
        log = AnalyticsLogDB(
            event_type=f"clickstream_{event.event_type}",
            user_type=event.user_role,
            details={
                "page": event.page,
                "action": event.action,
                "student_id": event.student_id,
                "session_id": event.session_id,
                **(event.metadata or {}),
            },
        )
        db.add(log)
    db.commit()
    return {"status": "tracked", "count": len(batch.events)}


# --------------- Analytics queries ---------------

@router.get("/analytics")
def get_clickstream_analytics(days: int = 7, db: Session = Depends(get_db)):
    """Aggregated clickstream analytics for the dashboard."""
    since = datetime.utcnow() - timedelta(days=days)
    events = (
        db.query(AnalyticsLogDB)
        .filter(
            AnalyticsLogDB.event_type.like("clickstream_%"),
            AnalyticsLogDB.created_at >= since,
        )
        .all()
    )

    if not events:
        return {
            "total_events": 0, "period_days": days,
            "page_views": {}, "actions": {}, "user_roles": {},
            "hourly_distribution": {}, "engagement_by_page": {},
            "top_actions": [], "session_count": 0,
        }

    # Page view counts
    page_views = Counter()
    actions = Counter()
    user_roles = Counter()
    hourly = Counter()
    sessions = set()
    page_time = {}  # page -> list of timestamps for engagement calc

    for e in events:
        details = e.details or {}
        page = details.get("page", "unknown")
        action = details.get("action")
        role = e.user_type or "unknown"
        session_id = details.get("session_id")

        if "page_view" in e.event_type:
            page_views[page] += 1
        if action:
            actions[action] += 1
        user_roles[role] += 1
        hourly[e.created_at.hour] += 1
        if session_id:
            sessions.add(session_id)

        if page not in page_time:
            page_time[page] = []
        page_time[page].append(e.created_at)

    # Engagement: avg events per page
    engagement = {page: len(timestamps) for page, timestamps in page_time.items()}

    # Top actions
    top_actions = [{"action": a, "count": c} for a, c in actions.most_common(15)]

    return {
        "total_events": len(events),
        "period_days": days,
        "page_views": dict(page_views.most_common()),
        "actions": dict(actions.most_common()),
        "user_roles": dict(user_roles),
        "hourly_distribution": {str(h): c for h, c in sorted(hourly.items())},
        "engagement_by_page": engagement,
        "top_actions": top_actions,
        "session_count": len(sessions),
    }


@router.get("/analytics/flow")
def get_user_flow(days: int = 7, db: Session = Depends(get_db)):
    """Page-to-page navigation flow for funnel analysis."""
    since = datetime.utcnow() - timedelta(days=days)
    events = (
        db.query(AnalyticsLogDB)
        .filter(
            AnalyticsLogDB.event_type == "clickstream_page_view",
            AnalyticsLogDB.created_at >= since,
        )
        .order_by(AnalyticsLogDB.created_at.asc())
        .all()
    )

    # Group by session, build page transitions
    session_pages = {}
    for e in events:
        details = e.details or {}
        sid = details.get("session_id", "unknown")
        page = details.get("page", "unknown")
        if sid not in session_pages:
            session_pages[sid] = []
        session_pages[sid].append(page)

    # Count transitions
    transitions = Counter()
    for pages in session_pages.values():
        for i in range(len(pages) - 1):
            transitions[(pages[i], pages[i + 1])] += 1

    flow = [
        {"from": f, "to": t, "count": c}
        for (f, t), c in transitions.most_common(20)
    ]

    # Entry pages (first page per session)
    entry_pages = Counter(pages[0] for pages in session_pages.values() if pages)

    return {
        "transitions": flow,
        "entry_pages": dict(entry_pages.most_common()),
        "total_sessions": len(session_pages),
    }
