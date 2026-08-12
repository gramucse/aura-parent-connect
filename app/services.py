
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from .db_models import Student, ParentSession, MentorCallback, CallLog

def normalize_phone(phone):
    if not phone: return None
    digits = "".join(ch for ch in str(phone) if ch.isdigit())
    return digits[-10:] if len(digits) >= 10 else digits

def normalize_student_id(student_id):
    if not student_id: return None
    return "".join(ch for ch in str(student_id).upper().strip() if ch.isalnum())

def get_student(db: Session, student_id):
    sid = normalize_student_id(student_id)
    return db.get(Student, sid) if sid else None

def student_summary(s: Student):
    completion_pct = round(100*s.coding_completed/max(s.coding_assigned,1))
    engagement = round(
        s.attendance_percentage*0.30 + s.training_percentage*0.20 +
        s.coding_score*0.25 + completion_pct*0.15 + s.campus_regularity_score*0.10
    )
    return {
        "student_id":s.student_id,"student_name":s.student_name,
        "attendance":{"percentage":s.attendance_percentage,"attended":s.attendance_attended,"held":s.attendance_held},
        "coding":{"score":s.coding_score,"assigned":s.coding_assigned,"completed":s.coding_completed,
                  "previous_week_score":s.coding_previous_week,"strong_topics":s.strong_topics or [],
                  "weak_topics":s.weak_topics or []},
        "training":{"percentage":s.training_percentage,"attended":s.training_attended,"held":s.training_held},
        "campus":{"present_today":s.present_today,"entry_time":s.entry_time,
                  "previous_day_entry_time":s.previous_day_entry_time,"regularity_score":s.campus_regularity_score},
        "mentor":{"name":s.mentor_name},"engagement_score":engagement
    }

def verify_parent(db, student_id, caller_number, last4):
    s = get_student(db, student_id)
    if not s: return False, "Student record not found.", None
    registered = normalize_phone(s.parent_mobile)
    incoming = normalize_phone(caller_number)
    if incoming and registered and incoming == registered:
        return True, "Parent verified using registered caller number.", s
    if last4 and registered and registered.endswith(str(last4).strip()):
        return True, "Parent verified using registered mobile last four digits.", s
    return False, "Verification failed. Please confirm the registered parent mobile details.", None

def upsert_session(db, call_id, caller_number=None, verified=None, student_id=None, language=None):
    x = db.get(ParentSession, call_id)
    if not x:
        x = ParentSession(call_id=call_id, caller_number=caller_number); db.add(x)
    if caller_number is not None: x.caller_number=caller_number
    if verified is not None: x.verified=verified
    if student_id is not None: x.verified_student_id=student_id
    if language: x.language=language
    x.updated_at=datetime.utcnow(); db.commit(); db.refresh(x); return x

def create_callback(db, student, concern, caller_number, call_id):
    x = MentorCallback(student_id=student.student_id, student_name=student.student_name,
        mentor_name=student.mentor_name, concern=concern[:1000], caller_number=caller_number,
        call_id=call_id, status="Pending")
    db.add(x); db.commit(); db.refresh(x); return x

def log_event(db, call_id, caller_number=None, student_id=None, event_type="tool",
              tool_name=None, success=True, language=None, detail=None):
    x = CallLog(call_id=call_id, caller_number=caller_number, student_id=student_id,
        event_type=event_type, tool_name=tool_name, success=success, language=language,
        detail=detail[:2000] if detail else None)
    db.add(x); db.commit(); return x

def dashboard_metrics(db):
    return {
        "total_events": db.scalar(select(func.count()).select_from(CallLog)) or 0,
        "successful_events": db.scalar(select(func.count()).select_from(CallLog).where(CallLog.success==True)) or 0,
        "callbacks_pending": db.scalar(select(func.count()).select_from(MentorCallback).where(MentorCallback.status=="Pending")) or 0,
        "sessions": db.scalar(select(func.count()).select_from(ParentSession)) or 0,
        "verified_sessions": db.scalar(select(func.count()).select_from(ParentSession).where(ParentSession.verified==True)) or 0,
        "students": db.scalar(select(func.count()).select_from(Student)) or 0,
    }

def validate_student_payload(data):
    errors=[]
    for field in ["student_id","student_name","parent_name","parent_mobile","mentor_name"]:
        if not str(data.get(field,"")).strip():
            errors.append(f"{field} is required")
    phone=normalize_phone(data.get("parent_mobile"))
    if phone and len(phone)<10: errors.append("parent_mobile must contain at least 10 digits")
    for field in ["attendance_percentage","coding_score","training_percentage","campus_regularity_score"]:
        try:
            v=int(data.get(field,0) or 0)
            if not 0<=v<=100: errors.append(f"{field} must be between 0 and 100")
        except: errors.append(f"{field} must be an integer")
    for field in ["attendance_attended","attendance_held","coding_assigned","coding_completed",
                  "coding_previous_week","training_attended","training_held"]:
        try: int(data.get(field,0) or 0)
        except: errors.append(f"{field} must be an integer")
    return errors

def upsert_student(db, data):
    sid=normalize_student_id(data["student_id"])
    s=db.get(Student,sid); created=s is None
    if created:
        s=Student(student_id=sid); db.add(s)
    s.student_name=str(data["student_name"]).strip()
    s.parent_name=str(data["parent_name"]).strip()
    s.parent_mobile=str(data["parent_mobile"]).strip()
    s.mentor_name=str(data["mentor_name"]).strip()
    for field in ["attendance_percentage","attendance_attended","attendance_held","coding_score","coding_assigned",
                  "coding_completed","coding_previous_week","training_percentage","training_attended",
                  "training_held","campus_regularity_score"]:
        setattr(s,field,int(data.get(field,0) or 0))
    s.strong_topics=data.get("strong_topics") or []
    s.weak_topics=data.get("weak_topics") or []
    p=data.get("present_today",False)
    if isinstance(p,str): p=p.strip().lower() in {"true","1","yes","y"}
    s.present_today=bool(p)
    s.entry_time=data.get("entry_time") or None
    s.previous_day_entry_time=data.get("previous_day_entry_time") or None
    db.commit(); db.refresh(s); return s,created
