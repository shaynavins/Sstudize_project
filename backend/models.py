from datetime import datetime, date
from typing import Dict, List, Optional

from sqlalchemy import (
 Column, Integer, String, Float, Text, DateTime, Date,
 Boolean, ForeignKey, JSON,
)
from sqlalchemy.orm import declarative_base, relationship
from pydantic import BaseModel, Field

Base = declarative_base()

#sqlalchemy: how the data is stored, pydantic models: how data is sent/received
#SQLAlchemy is object relational mapper or ORM 
#pydantic is python library for data validation and parsing. basically, parsing and structuring of output data  

class StudentDB(Base):
 __tablename__ = "students"

 id = Column(Integer, primary_key=True, autoincrement=True)
 name = Column(String(100), nullable=False)
 grade = Column(String(20), nullable=False) 
 exam_target = Column(String(50), nullable=False) 
 target_score = Column(Float, nullable=False)
 current_score = Column(Float, default=0.0)
 study_hours_per_day = Column(Float, default=6.0)
 subjects = Column(JSON, nullable=False) 
 strengths = Column(JSON, default=list) 
 weaknesses = Column(JSON, default=list) 
 created_at = Column(DateTime, default=datetime.utcnow)
 updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

 performance_metrics = relationship("PerformanceMetricDB", back_populates="student", cascade="all, delete-orphan")
 roadmaps = relationship("RoadmapDB", back_populates="student", cascade="all, delete-orphan")
 feedbacks = relationship("FeedbackDB", back_populates="student", cascade="all, delete-orphan")
 tasks = relationship("StudyTaskDB", back_populates="student", cascade="all, delete-orphan")


class PerformanceMetricDB(Base):
 __tablename__ = "performance_metrics"

 id = Column(Integer, primary_key=True, autoincrement=True)
 student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
 subject = Column(String(50), nullable=False)
 topic = Column(String(100), nullable=False)
 score = Column(Float, nullable=False) 
 max_score = Column(Float, default=100.0)
 test_type = Column(String(50), default="practice")
 date_taken = Column(Date, default=date.today)
 time_spent_minutes = Column(Integer, default=0)
 created_at = Column(DateTime, default=datetime.utcnow)

 student = relationship("StudentDB", back_populates="performance_metrics")


class RoadmapDB(Base):
 __tablename__ = "roadmaps"

 id = Column(Integer, primary_key=True, autoincrement=True)
 student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
 week_number = Column(Integer, nullable=False)
 start_date = Column(Date, nullable=False)
 end_date = Column(Date, nullable=False)
 goals = Column(JSON, nullable=False) 
 status = Column(String(20), default="active") 
 ai_generated = Column(Boolean, default=True)
 approved_by_teacher = Column(Boolean, default=False)
 created_at = Column(DateTime, default=datetime.utcnow)
 updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

 student = relationship("StudentDB", back_populates="roadmaps")


class StudyTaskDB(Base):
 __tablename__ = "study_tasks"

 id = Column(Integer, primary_key=True, autoincrement=True)
 student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
 roadmap_id = Column(Integer, ForeignKey("roadmaps.id"), nullable=True)
 subject = Column(String(50), nullable=False)
 topic = Column(String(100), nullable=False)
 description = Column(Text, nullable=False)
 task_type = Column(String(30), default="study")
 priority = Column(String(10), default="medium") 
 estimated_hours = Column(Float, default=1.0)
 actual_hours = Column(Float, default=0.0)
 scheduled_date = Column(Date, nullable=False)
 completed = Column(Boolean, default=False)
 completed_at = Column(DateTime, nullable=True)
 resources = Column(JSON, default=list)
 created_at = Column(DateTime, default=datetime.utcnow)

 student = relationship("StudentDB", back_populates="tasks")


class SWOTAnalysisDB(Base):
 __tablename__ = "swot_analyses"

 id = Column(Integer, primary_key=True, autoincrement=True)
 student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
 strengths = Column(JSON, nullable=False)
 weaknesses = Column(JSON, nullable=False)
 opportunities = Column(JSON, nullable=False)
 challenges = Column(JSON, nullable=False)
 action_plan = Column(JSON, nullable=False) 
 created_at = Column(DateTime, default=datetime.utcnow)


class FeedbackDB(Base):
 __tablename__ = "feedbacks"

 id = Column(Integer, primary_key=True, autoincrement=True)
 student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
 source = Column(String(20), nullable=False)
 feedback_type = Column(String(30), nullable=False)
 content = Column(JSON, nullable=False) 
 status = Column(String(20), default="pending") 
 resolved = Column(Boolean, default=False)
 created_at = Column(DateTime, default=datetime.utcnow)

 student = relationship("StudentDB", back_populates="feedbacks")


class WeeklyReportDB(Base):
 __tablename__ = "weekly_reports"

 id = Column(Integer, primary_key=True, autoincrement=True)
 student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
 week_number = Column(Integer, nullable=False)
 tasks_completed = Column(Integer, default=0)
 tasks_pending = Column(Integer, default=0)
 tasks_overdue = Column(Integer, default=0)
 adherence_score = Column(Float, default=0.0) 
 deviations = Column(JSON, default=list) 
 recommendations = Column(JSON, default=list) 
 agent_notes = Column(Text, nullable=True) 
 created_at = Column(DateTime, default=datetime.utcnow)


class AnalyticsLogDB(Base):
 __tablename__ = "analytics_logs"

 id = Column(Integer, primary_key=True, autoincrement=True)
 event_type = Column(String(50), nullable=False) 
 user_type = Column(String(20), default="student") 
 details = Column(JSON, default=dict)
 duration_ms = Column(Float, nullable=True)
 created_at = Column(DateTime, default=datetime.utcnow)


class StudentCreate(BaseModel):
 name: str
 grade: str
 exam_target: str
 target_score: float
 current_score: float = 0.0
 study_hours_per_day: float = 6.0
 subjects: Dict[str, float] 
 strengths: List[str] = []
 weaknesses: List[str] = []


class StudentUpdate(BaseModel):
 name: Optional[str] = None
 grade: Optional[str] = None
 exam_target: Optional[str] = None
 target_score: Optional[float] = None
 current_score: Optional[float] = None
 study_hours_per_day: Optional[float] = None
 subjects: Optional[Dict[str, float]] = None
 strengths: Optional[List[str]] = None
 weaknesses: Optional[List[str]] = None


class StudentResponse(BaseModel):
 id: int
 name: str
 grade: str
 exam_target: str
 target_score: float
 current_score: float
 study_hours_per_day: float
 subjects: Dict[str, float]
 strengths: List[str]
 weaknesses: List[str]
 created_at: datetime
 updated_at: datetime

 model_config = {"from_attributes": True}


class PerformanceMetricCreate(BaseModel):
 student_id: int
 subject: str
 topic: str
 score: float
 max_score: float = 100.0
 test_type: str = "practice"
 date_taken: date = Field(default_factory=date.today)
 time_spent_minutes: int = 0


class PerformanceMetricResponse(BaseModel):
 id: int
 student_id: int
 subject: str
 topic: str
 score: float
 max_score: float
 test_type: str
 date_taken: date
 time_spent_minutes: int

 model_config = {"from_attributes": True}


class StudyTaskCreate(BaseModel):
 student_id: int
 roadmap_id: Optional[int] = None
 subject: str
 topic: str
 description: str
 task_type: str = "study"
 priority: str = "medium"
 estimated_hours: float = 1.0
 scheduled_date: date
 resources: List[dict] = []


class StudyTaskResponse(BaseModel):
 id: int
 student_id: int
 roadmap_id: Optional[int]
 subject: str
 topic: str
 description: str
 task_type: str
 priority: str
 estimated_hours: float
 actual_hours: float
 scheduled_date: date
 completed: bool
 completed_at: Optional[datetime]
 resources: List[dict]

 model_config = {"from_attributes": True}


class FeedbackCreate(BaseModel):
 student_id: int
 source: str 
 feedback_type: str 
 content: dict


class FeedbackResponse(BaseModel):
 id: int
 student_id: int
 source: str
 feedback_type: str
 content: dict
 status: str
 resolved: bool
 created_at: datetime

 model_config = {"from_attributes": True}


class SWOTResponse(BaseModel):
 id: int
 student_id: int
 strengths: List[dict]
 weaknesses: List[dict]
 opportunities: List[dict]
 challenges: List[dict]
 action_plan: List[dict]
 created_at: datetime

 model_config = {"from_attributes": True}


class WeeklyReportResponse(BaseModel):
 id: int
 student_id: int
 week_number: int
 tasks_completed: int
 tasks_pending: int
 tasks_overdue: int
 adherence_score: float
 deviations: List[dict]
 recommendations: List[dict]
 agent_notes: Optional[str]
 created_at: datetime

 model_config = {"from_attributes": True}


class RoadmapResponse(BaseModel):
 id: int
 student_id: int
 week_number: int
 start_date: date
 end_date: date
 goals: List[str]
 status: str
 ai_generated: bool
 approved_by_teacher: bool
 created_at: datetime

 model_config = {"from_attributes": True}
