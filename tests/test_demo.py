\
import os
os.environ["AURA_TOOL_API_KEY"] = "test-key"

from app.store import get_student, verify_parent, engagement_score
from app.gemini_service import fallback_explanation

def test_student_exists():
    s = get_student("23A91A0501")
    assert s and s["student_name"] == "Rahul Kumar"

def test_parent_last4_verification():
    ok, _, s = verify_parent("23A91A0501", last4="4582")
    assert ok and s["student_name"] == "Rahul Kumar"

def test_wrong_verification():
    ok, _, _ = verify_parent("23A91A0501", last4="0000")
    assert not ok

def test_engagement_score_range():
    score = engagement_score(get_student("23A91A0501"))
    assert 0 <= score <= 100

def test_fallback_answer_uses_real_data():
    s = get_student("23A91A0501")
    answer = fallback_explanation(s, "How is coding?")
    assert "76%" in answer and "38" in answer
