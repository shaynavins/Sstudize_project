import json
import os
from datetime import date
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from backend.models import (
    Base, StudentDB, PerformanceMetricDB, StudyTaskDB, RoadmapDB,
)

DB_PATH = Path(__file__).parent.parent / "sstudize.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_sample_data():
    db = SessionLocal()
    try:
        if db.query(StudentDB).count() > 0:
            return

        sample_path = Path(__file__).parent.parent / "data" / "sample_data.json"
        if not sample_path.exists():
            print("No sample_data.json found, skipping seed")
            return

        with open(sample_path, "r") as f:
            data = json.load(f)

        for student_data in data.get("students", []):
            metrics_data = student_data.pop("performance_metrics", [])
            tasks_data = student_data.pop("tasks", [])

            student = StudentDB(**student_data)
            db.add(student)
            db.flush()

            for metric in metrics_data:
                metric["student_id"] = student.id
                if isinstance(metric.get("date_taken"), str):
                    metric["date_taken"] = date.fromisoformat(metric["date_taken"])
                db.add(PerformanceMetricDB(**metric))

            for task in tasks_data:
                task["student_id"] = student.id
                if isinstance(task.get("scheduled_date"), str):
                    task["scheduled_date"] = date.fromisoformat(task["scheduled_date"])
                db.add(StudyTaskDB(**task))

        db.commit()
        print(f"Seeded {len(data.get('students', []))} sample students")

    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
    finally:
        db.close()
