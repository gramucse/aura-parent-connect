\
import json
from pathlib import Path
from datetime import datetime
from threading import Lock

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "students.json"
CALLBACK_PATH = Path(__file__).resolve().parent.parent / "data" / "callbacks.json"
_lock = Lock()

def _students():
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))

def get_student(student_id: str):
    sid = student_id.strip().upper()
    return next((s for s in _students() if s["student_id"].upper() == sid), None)

def normalize_phone(phone: str | None):
    if not phone:
        return None
    digits = "".join(ch for ch in phone if ch.isdigit())
    return digits[-10:] if len(digits) >= 10 else digits

def verify_parent(student_id: str, caller_number: str | None = None, last4: str | None = None):
    student = get_student(student_id)
    if not student:
        return False, "Student record not found.", None

    registered = normalize_phone(student["parent_mobile"])
    incoming = normalize_phone(caller_number)

    if incoming and registered and incoming == registered:
        return True, "Parent verified using registered caller number.", student

    if last4 and registered and registered.endswith(last4):
        return True, "Parent verified using registered mobile last four digits.", student

    return False, "Verification failed. Please use the registered parent number or provide the correct last four digits.", None

def engagement_score(student: dict):
    a = student["attendance"]["percentage"]
    t = student["training"]["percentage"]
    c = student["coding"]["score"]
    p = round(100 * student["coding"]["completed"] / max(student["coding"]["assigned"], 1))
    g = student["campus"]["regularity_score"]
    return round(a * 0.30 + t * 0.20 + c * 0.25 + p * 0.15 + g * 0.10)

def safe_summary(student: dict):
    return {
        "student_id": student["student_id"],
        "student_name": student["student_name"],
        "attendance": student["attendance"],
        "coding": student["coding"],
        "training": student["training"],
        "campus": student["campus"],
        "mentor": student["mentor"],
        "engagement_score": engagement_score(student),
    }

def create_callback(student: dict, concern: str, caller_number: str | None):
    item = {
        "student_id": student["student_id"],
        "student_name": student["student_name"],
        "mentor_name": student["mentor"]["name"],
        "concern": concern.strip()[:500],
        "caller_number": caller_number,
        "status": "Pending",
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    with _lock:
        existing = []
        if CALLBACK_PATH.exists():
            try:
                existing = json.loads(CALLBACK_PATH.read_text(encoding="utf-8"))
            except Exception:
                existing = []
        existing.append(item)
        CALLBACK_PATH.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    return item
