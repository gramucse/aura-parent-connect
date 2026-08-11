\
import os
from fastapi import FastAPI, HTTPException, Header
from dotenv import load_dotenv

from .models import (
    VerifyRequest,
    ExplainRequest,
    CallbackRequest,
    RetellToolRequest,
    RetellEnvelope,
)
from .gemini_service import explain

load_dotenv()
app = FastAPI(
    title=os.getenv("APP_NAME", "AURA Parent Connect"),
    version="0.1.0",
    description="Demo backend for a multilingual parent voice agent."
)

def require_tool_key(x_aura_api_key: str | None):
    expected = os.getenv("AURA_TOOL_API_KEY", "change-me-for-demo")
    if expected and x_aura_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid AURA tool API key")

@app.get("/")
def root():
    return {
        "name": "AURA Parent Connect",
        "status": "ready",
        "demo": True,
        "docs": "/docs"
    }

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/verify-parent")
def api_verify_parent(payload: VerifyRequest):
    ok, message, student = verify_parent(
        payload.student_id, payload.caller_number, payload.parent_mobile_last4
    )
    return {
        "verified": ok,
        "message": message,
        "student_name": student["student_name"] if student else None
    }

@app.get("/student/{student_id}/summary")
def api_summary(student_id: str):
    student = get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return safe_summary(student)

@app.post("/student/explain")
def api_explain(payload: ExplainRequest):
    student = get_student(payload.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    answer, engine = explain(safe_summary(student), payload.question, payload.language)
    return {"answer": answer, "engine": engine}

@app.post("/student/callback")
def api_callback(payload: CallbackRequest):
    student = get_student(payload.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    item = create_callback(student, payload.concern, payload.caller_number)
    return {"created": True, "callback": item}

# -------- Retell custom-function endpoints --------
# Protect these with X-AURA-API-Key. Configure the same header in Retell.

@app.post("/tools/verify-parent")
def tool_verify_parent(
    payload: RetellEnvelope,
    x_aura_api_key: str | None = Header(default=None)
):
    require_tool_key(x_aura_api_key)

    data = payload.args

    student_id = data.get("student_id")
    caller_number = data.get("caller_number")
    parent_mobile_last4 = data.get("parent_mobile_last4")

    if not student_id:
        return {
            "verified": False,
            "message": "Student registration number was not received."
        }

    ok, message, student = verify_parent(
        student_id,
        caller_number,
        parent_mobile_last4
    )

    return {
        "verified": ok,
        "message": message,
        "student_id": student["student_id"] if student else None,
        "student_name": student["student_name"] if student else None,
    }

@app.post("/tools/student-summary")
def tool_student_summary(payload: RetellToolRequest, x_aura_api_key: str | None = Header(default=None)):
    require_tool_key(x_aura_api_key)
    student = get_student(payload.student_id)
    if not student:
        return {"found": False, "message": "Student record not found."}
    return {"found": True, "student": safe_summary(student)}

@app.post("/tools/explain")
def tool_explain(payload: RetellToolRequest, x_aura_api_key: str | None = Header(default=None)):
    require_tool_key(x_aura_api_key)
    student = get_student(payload.student_id)
    if not student:
        return {"found": False, "answer": "Student record not found."}
    answer, engine = explain(safe_summary(student), payload.question or "Give an overall performance summary.", payload.language)
    return {"found": True, "answer": answer, "engine": engine}

@app.post("/tools/request-callback")
def tool_request_callback(payload: RetellToolRequest, x_aura_api_key: str | None = Header(default=None)):
    require_tool_key(x_aura_api_key)
    student = get_student(payload.student_id)
    if not student:
        return {"created": False, "message": "Student record not found."}
    item = create_callback(student, payload.concern or "Parent requested mentor callback", payload.caller_number)
    return {"created": True, "message": f"Callback request created for mentor {student['mentor']['name']}.", "callback": item}
