\
import os
from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import select

from .database import Base, engine, get_db, SessionLocal
from .db_models import Student, MentorCallback, CallLog
from .schemas import VerifyRequest, ExplainRequest, CallbackRequest, CallbackStatusRequest, RetellEnvelope
from .services import (
    get_student, verify_parent, student_summary, create_callback,
    upsert_session, log_event, dashboard_metrics
)
from .gemini_service import explain
from .seed import seed_students

app = FastAPI(
    title=os.getenv("APP_NAME", "Aditya University Parent Connect"),
    version="2.0.0",
    description="AURA Parent Connect v2: Retell + Gemini + DB + mentor dashboard."
)

templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_students(db)
    finally:
        db.close()

def require_tool_key(x_aura_api_key: str | None):
    expected = os.getenv("AURA_TOOL_API_KEY", "change-me")
    if expected and x_aura_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid AURA tool API key")

def retell_call_id(payload: RetellEnvelope):
    call = payload.call or {}
    return call.get("call_id") or call.get("id") or "web-test"

def retell_caller(payload: RetellEnvelope):
    call = payload.call or {}
    return call.get("from_number") or call.get("user_number") or call.get("caller_number")

@app.get("/")
def root():
    return {
        "name": os.getenv("APP_NAME", "Aditya University Parent Connect"),
        "version": "2.0.0",
        "status": "ready",
        "docs": "/docs",
        "dashboard": "/dashboard"
    }

@app.get("/health")
def health():
    return {"ok": True, "version": "2.0.0"}

# -------- Direct API testing --------

@app.post("/verify-parent")
def api_verify_parent(payload: VerifyRequest, db: Session = Depends(get_db)):
    ok, message, student = verify_parent(db, payload.student_id, payload.caller_number, payload.parent_mobile_last4)
    return {
        "verified": ok,
        "message": message,
        "student_id": student.student_id if student else None,
        "student_name": student.student_name if student else None
    }

@app.get("/student/{student_id}/summary")
def api_summary(student_id: str, db: Session = Depends(get_db)):
    student = get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student_summary(student)

@app.post("/student/explain")
def api_explain(payload: ExplainRequest, db: Session = Depends(get_db)):
    student = get_student(db, payload.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    answer, engine_name = explain(student_summary(student), payload.question, payload.language)
    return {"answer": answer, "engine": engine_name}

@app.post("/student/callback")
def api_callback(payload: CallbackRequest, db: Session = Depends(get_db)):
    student = get_student(db, payload.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    item = create_callback(db, student, payload.concern, payload.caller_number, payload.call_id)
    return {"created": True, "callback_id": item.id, "status": item.status}

# -------- Retell tools --------

@app.post("/tools/verify-parent")
def tool_verify_parent(payload: RetellEnvelope, x_aura_api_key: str | None = Header(default=None),
                       db: Session = Depends(get_db)):
    require_tool_key(x_aura_api_key)
    data = payload.args or {}
    call_id = retell_call_id(payload)
    caller = data.get("caller_number") or retell_caller(payload)

    student_id = data.get("student_id")
    last4 = data.get("parent_mobile_last4")

    ok, message, student = verify_parent(db, student_id, caller, last4)
    upsert_session(
        db, call_id, caller_number=caller, verified=ok,
        student_id=student.student_id if student else None
    )
    log_event(
        db, call_id, caller, student.student_id if student else student_id,
        tool_name="verify_parent", success=ok, detail=message
    )

    return {
        "verified": ok,
        "message": message,
        "student_id": student.student_id if student else None,
        "student_name": student.student_name if student else None
    }

@app.post("/tools/student-summary")
def tool_student_summary(payload: RetellEnvelope, x_aura_api_key: str | None = Header(default=None),
                         db: Session = Depends(get_db)):
    require_tool_key(x_aura_api_key)
    data = payload.args or {}
    call_id = retell_call_id(payload)
    student_id = data.get("student_id")
    student = get_student(db, student_id)

    if not student:
        log_event(db, call_id, student_id=student_id, tool_name="student_summary", success=False, detail="Student not found")
        return {"found": False, "message": "Student record not found."}

    log_event(db, call_id, student_id=student.student_id, tool_name="student_summary", success=True)
    return {"found": True, "student": student_summary(student)}

@app.post("/tools/explain")
def tool_explain(payload: RetellEnvelope, x_aura_api_key: str | None = Header(default=None),
                 db: Session = Depends(get_db)):
    require_tool_key(x_aura_api_key)
    data = payload.args or {}
    call_id = retell_call_id(payload)

    student_id = data.get("student_id")
    question = data.get("question", "Give an overall performance summary.")
    language = data.get("language", "auto")

    student = get_student(db, student_id)
    if not student:
        log_event(db, call_id, student_id=student_id, tool_name="explain_student_performance",
                  success=False, language=language, detail="Student not found")
        return {"found": False, "answer": "Student record not found."}

    answer, engine_name = explain(student_summary(student), question, language)
    upsert_session(db, call_id, verified=True, student_id=student.student_id, language=language)
    log_event(db, call_id, student_id=student.student_id, tool_name="explain_student_performance",
              success=True, language=language, detail=question)

    return {"found": True, "answer": answer, "engine": engine_name}

@app.post("/tools/request-callback")
def tool_request_callback(payload: RetellEnvelope, x_aura_api_key: str | None = Header(default=None),
                          db: Session = Depends(get_db)):
    require_tool_key(x_aura_api_key)
    data = payload.args or {}
    call_id = retell_call_id(payload)

    student_id = data.get("student_id")
    concern = data.get("concern", "Parent requested mentor callback")
    caller = data.get("caller_number") or retell_caller(payload)

    student = get_student(db, student_id)
    if not student:
        log_event(db, call_id, caller, student_id, tool_name="request_callback", success=False, detail="Student not found")
        return {"created": False, "message": "Student record not found."}

    item = create_callback(db, student, concern, caller, call_id)
    log_event(db, call_id, caller, student.student_id, tool_name="request_callback", success=True, detail=concern)

    return {
        "created": True,
        "message": f"Callback request created for mentor {student.mentor_name}.",
        "callback_id": item.id,
        "status": item.status
    }

# -------- Retell generic webhook/event log --------

@app.post("/webhooks/retell")
async def retell_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    call = payload.get("call") or payload
    call_id = call.get("call_id") or payload.get("call_id") or "unknown"
    caller = call.get("from_number") or call.get("user_number")
    event = payload.get("event") or payload.get("event_type") or "webhook"
    log_event(db, call_id, caller_number=caller, event_type=str(event), tool_name=None, success=True,
              detail=str(payload)[:1800])
    return {"received": True}

# -------- Mentor dashboard --------

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, admin_key: str | None = None, db: Session = Depends(get_db)):
    expected = os.getenv("ADMIN_KEY", "admin-demo-key")
    if expected and admin_key != expected:
        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "authorized": False,
                "metrics": {},
                "callbacks": [],
                "logs": []
            },
            status_code=401,
        )

    metrics = dashboard_metrics(db)
    callbacks = db.execute(select(MentorCallback).order_by(MentorCallback.created_at.desc()).limit(50)).scalars().all()
    logs = db.execute(select(CallLog).order_by(CallLog.created_at.desc()).limit(80)).scalars().all()
    return templates.TemplateResponse(
    request=request,
    name="dashboard.html",
    context={
        "authorized": True,
        "metrics": metrics,
        "callbacks": callbacks,
        "logs": logs
    }
    )

@app.post("/admin/callbacks/{callback_id}/status")
def update_callback_status(callback_id: int, payload: CallbackStatusRequest,
                           x_admin_key: str | None = Header(default=None),
                           db: Session = Depends(get_db)):
    if x_admin_key != os.getenv("ADMIN_KEY", "admin-demo-key"):
        raise HTTPException(status_code=401, detail="Invalid admin key")
    item = db.get(MentorCallback, callback_id)
    if not item:
        raise HTTPException(status_code=404, detail="Callback not found")
    allowed = {"Pending", "Contacted", "Resolved"}
    if payload.status not in allowed:
        raise HTTPException(status_code=400, detail=f"Status must be one of {sorted(allowed)}")
    item.status = payload.status
    db.commit()
    return {"updated": True, "callback_id": callback_id, "status": item.status}
