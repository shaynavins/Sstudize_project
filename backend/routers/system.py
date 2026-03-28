import os
import time
from datetime import datetime, timedelta
from collections import Counter, defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db, SessionLocal
from backend.models import AnalyticsLogDB

router = APIRouter(prefix="/api/system", tags=["System Monitoring"])

_start_time = time.time()


# --------------- Health checks ---------------

@router.get("/health")
def health_check():
    """Liveness probe for load balancers / container orchestrators."""
    db_ok = False
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_ok = True
    except Exception:
        pass
    uptime_seconds = round(time.time() - _start_time, 1)
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "error",
        "uptime_seconds": uptime_seconds,
        "uptime_human": _format_uptime(uptime_seconds),
        "pid": os.getpid(),
        "timestamp": datetime.utcnow().isoformat(),
    }


def _format_uptime(seconds):
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h}h {m}m {s}s"


# --------------- API Performance ---------------

@router.get("/performance")
def get_api_performance(days: int = 7, db: Session = Depends(get_db)):
    """API response time analytics: avg/p95/max per endpoint, overall stats."""
    since = datetime.utcnow() - timedelta(days=days)
    logs = (
        db.query(AnalyticsLogDB)
        .filter(
            AnalyticsLogDB.event_type == "api_call",
            AnalyticsLogDB.created_at >= since,
            AnalyticsLogDB.duration_ms.isnot(None),
        )
        .all()
    )

    if not logs:
        return {"total_requests": 0, "period_days": days, "endpoints": [], "status_breakdown": {}, "overall": {}}

    # Group by endpoint
    endpoint_data = defaultdict(list)
    status_counts = Counter()
    all_durations = []

    for log in logs:
        details = log.details or {}
        path = details.get("path", "unknown")
        status = details.get("status", 0)
        duration = log.duration_ms or 0

        # Skip clickstream/health polling from stats
        if "/clickstream/" in path or path == "/health":
            continue

        endpoint_data[path].append(duration)
        all_durations.append(duration)

        if status >= 500:
            status_counts["5xx"] += 1
        elif status >= 400:
            status_counts["4xx"] += 1
        elif status >= 200:
            status_counts["2xx"] += 1

    # Per-endpoint stats
    endpoints = []
    for path, durations in sorted(endpoint_data.items(), key=lambda x: -max(x[1])):
        sorted_d = sorted(durations)
        p95_idx = int(len(sorted_d) * 0.95)
        endpoints.append({
            "path": path,
            "requests": len(durations),
            "avg_ms": round(sum(durations) / len(durations), 1),
            "p95_ms": round(sorted_d[min(p95_idx, len(sorted_d) - 1)], 1),
            "max_ms": round(max(durations), 1),
            "min_ms": round(min(durations), 1),
        })

    # Overall
    sorted_all = sorted(all_durations) if all_durations else [0]
    p95_idx = int(len(sorted_all) * 0.95)

    return {
        "total_requests": len(all_durations),
        "period_days": days,
        "endpoints": endpoints[:20],
        "status_breakdown": dict(status_counts),
        "overall": {
            "avg_ms": round(sum(all_durations) / max(len(all_durations), 1), 1),
            "p95_ms": round(sorted_all[min(p95_idx, len(sorted_all) - 1)], 1),
            "max_ms": round(max(all_durations), 1) if all_durations else 0,
        },
    }


# --------------- Error Log ---------------

@router.get("/errors")
def get_error_log(days: int = 7, limit: int = 50, db: Session = Depends(get_db)):
    """Recent errors with tracebacks."""
    since = datetime.utcnow() - timedelta(days=days)
    errors = (
        db.query(AnalyticsLogDB)
        .filter(
            AnalyticsLogDB.event_type == "api_error",
            AnalyticsLogDB.created_at >= since,
        )
        .order_by(AnalyticsLogDB.created_at.desc())
        .limit(limit)
        .all()
    )

    error_list = []
    error_by_path = Counter()
    for e in errors:
        details = e.details or {}
        error_list.append({
            "timestamp": e.created_at.isoformat(),
            "path": details.get("path", ""),
            "method": details.get("method", ""),
            "status": details.get("status", 0),
            "traceback": details.get("traceback", ""),
            "duration_ms": e.duration_ms,
        })
        error_by_path[details.get("path", "unknown")] += 1

    total_errors = (
        db.query(func.count(AnalyticsLogDB.id))
        .filter(AnalyticsLogDB.event_type == "api_error", AnalyticsLogDB.created_at >= since)
        .scalar()
    )

    return {
        "total_errors": total_errors,
        "period_days": days,
        "errors": error_list,
        "errors_by_endpoint": dict(error_by_path.most_common(10)),
    }


# --------------- Bottlenecks ---------------

@router.get("/bottlenecks")
def get_bottlenecks(days: int = 7, db: Session = Depends(get_db)):
    """Slow requests (>2s) and agent performance."""
    since = datetime.utcnow() - timedelta(days=days)

    # Slow requests
    slow = (
        db.query(AnalyticsLogDB)
        .filter(
            AnalyticsLogDB.event_type == "slow_request",
            AnalyticsLogDB.created_at >= since,
        )
        .order_by(AnalyticsLogDB.duration_ms.desc())
        .limit(20)
        .all()
    )
    slow_list = [{
        "timestamp": s.created_at.isoformat(),
        "path": (s.details or {}).get("path", ""),
        "method": (s.details or {}).get("method", ""),
        "duration_ms": round(s.duration_ms, 1) if s.duration_ms else 0,
    } for s in slow]

    # Agent performance
    agent_logs = (
        db.query(AnalyticsLogDB)
        .filter(
            AnalyticsLogDB.event_type == "agent_invocation",
            AnalyticsLogDB.created_at >= since,
        )
        .all()
    )
    agent_stats = defaultdict(lambda: {"durations": [], "successes": 0, "failures": 0})
    for a in agent_logs:
        details = a.details or {}
        name = details.get("agent", "unknown")
        if a.duration_ms:
            agent_stats[name]["durations"].append(a.duration_ms)
        if details.get("success"):
            agent_stats[name]["successes"] += 1
        else:
            agent_stats[name]["failures"] += 1

    agent_perf = []
    for name, stats in agent_stats.items():
        durations = stats["durations"]
        agent_perf.append({
            "agent": name,
            "total_runs": stats["successes"] + stats["failures"],
            "successes": stats["successes"],
            "failures": stats["failures"],
            "avg_ms": round(sum(durations) / max(len(durations), 1), 1),
            "max_ms": round(max(durations), 1) if durations else 0,
        })

    return {
        "slow_requests": slow_list,
        "slow_request_count": len(slow_list),
        "agent_performance": agent_perf,
        "period_days": days,
    }
