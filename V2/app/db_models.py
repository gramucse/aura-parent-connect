\
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base

class Student(Base):
    __tablename__ = "students"

    student_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    student_name: Mapped[str] = mapped_column(String(120), nullable=False)
    parent_name: Mapped[str] = mapped_column(String(120), nullable=False)
    parent_mobile: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    mentor_name: Mapped[str] = mapped_column(String(120), nullable=False)

    attendance_percentage: Mapped[int] = mapped_column(Integer, default=0)
    attendance_attended: Mapped[int] = mapped_column(Integer, default=0)
    attendance_held: Mapped[int] = mapped_column(Integer, default=0)

    coding_score: Mapped[int] = mapped_column(Integer, default=0)
    coding_assigned: Mapped[int] = mapped_column(Integer, default=0)
    coding_completed: Mapped[int] = mapped_column(Integer, default=0)
    coding_previous_week: Mapped[int] = mapped_column(Integer, default=0)
    strong_topics: Mapped[list] = mapped_column(JSON, default=list)
    weak_topics: Mapped[list] = mapped_column(JSON, default=list)

    training_percentage: Mapped[int] = mapped_column(Integer, default=0)
    training_attended: Mapped[int] = mapped_column(Integer, default=0)
    training_held: Mapped[int] = mapped_column(Integer, default=0)

    present_today: Mapped[bool] = mapped_column(Boolean, default=False)
    entry_time: Mapped[str | None] = mapped_column(String(30), nullable=True)
    previous_day_entry_time: Mapped[str | None] = mapped_column(String(30), nullable=True)
    campus_regularity_score: Mapped[int] = mapped_column(Integer, default=0)

class ParentSession(Base):
    __tablename__ = "parent_sessions"

    call_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    caller_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_student_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    language: Mapped[str] = mapped_column(String(20), default="auto")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class MentorCallback(Base):
    __tablename__ = "mentor_callbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[str] = mapped_column(String(40), ForeignKey("students.student_id"), index=True)
    student_name: Mapped[str] = mapped_column(String(120))
    mentor_name: Mapped[str] = mapped_column(String(120))
    concern: Mapped[str] = mapped_column(Text)
    caller_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    call_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="Pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class CallLog(Base):
    __tablename__ = "call_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    call_id: Mapped[str] = mapped_column(String(120), index=True)
    caller_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    student_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    event_type: Mapped[str] = mapped_column(String(40), default="tool")
    tool_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    language: Mapped[str | None] = mapped_column(String(20), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
