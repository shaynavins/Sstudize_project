from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    StudentDB, PerformanceMetricDB,
    StudentCreate, StudentUpdate, StudentResponse,
    PerformanceMetricCreate, PerformanceMetricResponse,
)

router = APIRouter(prefix="/api/students", tags=["Students"])


@router.get("/", response_model=List[StudentResponse])
def list_students(db: Session = Depends(get_db)):
    return db.query(StudentDB).all()


@router.get("/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(StudentDB).filter(StudentDB.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.post("/", response_model=StudentResponse, status_code=201)
def create_student(data: StudentCreate, db: Session = Depends(get_db)):
    student = StudentDB(**data.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.put("/{student_id}", response_model=StudentResponse)
def update_student(student_id: int, data: StudentUpdate, db: Session = Depends(get_db)):
    student = db.query(StudentDB).filter(StudentDB.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


@router.delete("/{student_id}", status_code=204)
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(StudentDB).filter(StudentDB.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(student)
    db.commit()


@router.get("/{student_id}/metrics", response_model=List[PerformanceMetricResponse])
def list_metrics(student_id: int, db: Session = Depends(get_db)):
    return (
        db.query(PerformanceMetricDB)
        .filter(PerformanceMetricDB.student_id == student_id)
        .order_by(PerformanceMetricDB.date_taken.desc())
        .all()
    )


@router.post("/{student_id}/metrics", response_model=PerformanceMetricResponse, status_code=201)
def add_metric(student_id: int, data: PerformanceMetricCreate, db: Session = Depends(get_db)):
    student = db.query(StudentDB).filter(StudentDB.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    metric = PerformanceMetricDB(**data.model_dump())
    metric.student_id = student_id
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric
