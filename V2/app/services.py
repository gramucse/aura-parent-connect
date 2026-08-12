\
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from .db_models import Student, ParentSession, MentorCallback, CallLog

def normalize_phone(phone: str | None):
    if not phone:
        return None
    digits = "".join(ch for ch in phone if ch.isdigit())
    return digits[-10:] if len(digits) >= 10 else digits

def normalize_student_id(student_id: str | None):
    if not student_id:
        return None
    return "".join(ch for ch in student_id.upper().strip() if ch.isalnum())

def get_student(db: Session, student_id: str | None):
    sid = normalize_student_id(student_id)
    if not sid:
        return None
    return db.get(Student, sid)

def student_summary(s: Student):
    completion_pct = round(100 * s.coding_completed / max(s.coding_assigned, 1))
    engagement = round(
        s.attendance_percentage * 0.30
        + s.training_percentage * 0.20
        + s.coding_score * 0.25
        + completion_pct * 0.15
        + s.campus_regularity_score * 0.10
    )
    return {
        "student_id": s.student_id,
        "student_name": s.student_name,
        "attendance": {
            "percentage": s.attendance_percentage,
            "attended": s.attendance_attended,
            "held": s.attendance_held,
        },
        "coding": {
            "score": s.coding_score,
            "assigned": s.coding_assigned,
            "completed": s.coding_completed,
            "previous_week_score": s.coding_previous_week,
            "strong_topics": s.strong_topics or [],
            "weak_topics": s.weak_topics or [],
        },
        "training": {
            "percentage": s.training_percentage,
            "attended": s.training_attended,
            "held": s.training_held,
        },
        "campus": {
            "present_today": s.present_today,
            "entry_time": s.entry_time,
            "previous_day_entry_time": s.previous_day_entry_time,
            "regularity_score": s.campus_regularity_score,
        },
        "mentor": {"name": s.mentor_name},
        "engagement_score": engagement,
    }

def verify_parent(db: Session, student_id: str, caller_number: str | None, last4: str | None):
    student = get_student(db, student_id)
    if not student:
        return False, "Student record not found.", None

    registered = normalize_phone(student.parent_mobile)
    incoming = normalize_phone(caller_number)

    if incoming and registered and incoming == registered:
        return True, "Parent verified using registered caller number.", student

    if last4 and registered and registered.endswith(str(last4).strip()):
        return True, "Parent verified using registered mobile last four digits.", student

    return False, "Verification failed. Please confirm the registered parent mobile details.", None

def upsert_session(db: Session, call_id: str, caller_number: str | None = None,
                   verified: bool | None = None, student_id: str | None = None,
                   language: str | None = None):
    session = db.get(ParentSession, call_id)
    if not session:
        session = ParentSession(call_id=call_id, caller_number=caller_number)
        db.add(session)
    if caller_number is not None:
        session.caller_number = caller_number
    if verified is not None:
        session.verified = verified
    if student_id is not None:
        session.verified_student_id = student_id
    if language:
        session.language = language
    session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(session)
    return session

def create_callback(db: Session, student: Student, concern: str,
                    caller_number: str | None, call_id: str | None):
    item = MentorCallback(
        student_id=student.student_id,
        student_name=student.student_name,
        mentor_name=student.mentor_name,
        concern=concern[:1000],
        caller_number=caller_number,
        call_id=call_id,
        status="Pending",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

def log_event(db: Session, call_id: str, caller_number: str | None = None,
              student_id: str | None = None, event_type: str = "tool",
              tool_name: str | None = None, success: bool = True,
              language: str | None = None, detail: str | None = None):
    item = CallLog(
        call_id=call_id,
        caller_number=caller_number,
        student_id=student_id,
        event_type=event_type,
        tool_name=tool_name,
        success=success,
        language=language,
        detail=detail[:2000] if detail else None,
    )
    db.add(item)
    db.commit()
    return item

def dashboard_metrics(db: Session):
    total_events = db.scalar(select(func.count()).select_from(CallLog)) or 0
    successful = db.scalar(select(func.count()).select_from(CallLog).where(CallLog.success == True)) or 0
    callbacks_pending = db.scalar(select(func.count()).select_from(MentorCallback).where(MentorCallback.status == "Pending")) or 0
    sessions = db.scalar(select(func.count()).select_from(ParentSession)) or 0
    verified_sessions = db.scalar(select(func.count()).select_from(ParentSession).where(ParentSession.verified == True)) or 0

    return {
        "total_events": total_events,
        "successful_events": successful,
        "callbacks_pending": callbacks_pending,
        "sessions": sessions,
        "verified_sessions": verified_sessions,
    }
