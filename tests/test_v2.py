\
import os
os.environ["DATABASE_URL"] = "sqlite:///./test_aura_v2.db"
os.environ["AURA_TOOL_API_KEY"] = "test-key"

from app.database import Base, engine, SessionLocal
from app.seed import seed_students
from app.services import get_student, verify_parent, student_summary

def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_students(db)
    db.close()

def test_seed():
    db = SessionLocal()
    s = get_student(db, "23A91A0501")
    assert s and s.student_name == "Rahul Kumar"
    db.close()

def test_verify_last4():
    db = SessionLocal()
    ok, _, s = verify_parent(db, "23A91A0501", None, "4582")
    assert ok and s.student_name == "Rahul Kumar"
    db.close()

def test_verify_wrong():
    db = SessionLocal()
    ok, _, _ = verify_parent(db, "23A91A0501", None, "0000")
    assert not ok
    db.close()

def test_summary():
    db = SessionLocal()
    summary = student_summary(get_student(db, "23A91A0501"))
    assert summary["attendance"]["percentage"] == 91
    assert summary["coding"]["score"] == 76
    db.close()
