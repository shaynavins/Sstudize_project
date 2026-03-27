from datetime import datetime
from backend.database import SessionLocal
from backend.models import AnalyticsLogDB

#sessionLocal is class of SQLAlchemy(ORM libr which usses python objects to query isnstead of raw SQL) to creeate db session instances for each incoming web request

def log_event(event_type, details=None, user_type="system", duration_ms=None):
    db = SessionLocal()
    try:
        log = AnalyticsLogDB(
            event_type=event_type,
            user_type=user_type,
            details=details or {},
            duration_ms=duration_ms,
        )
        db.add(log)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
