\
import os
import json
from dotenv import load_dotenv

load_dotenv()

SYSTEM_INSTRUCTION = """
You are AURA Parent Connect, a university parent-support assistant.

Rules:
1. Student facts supplied in STUDENT_DATA are the only source of truth.
2. Never invent marks, attendance, arrival times, reasons for absence, health data, fees, disciplinary issues, or personal information.
3. If the requested fact is absent, say it is currently unavailable.
4. Keep spoken answers concise: normally 2-4 sentences.
5. Explain numbers in a parent-friendly way and mention the clearest improvement area when appropriate.
6. Reply in the parent's language. Support English, Telugu, Hindi, and natural code-switching.
7. Never reveal another student's data.
8. Do not claim a mentor callback was created unless the callback tool/API confirms it.
"""

def fallback_explanation(student: dict, question: str):
    q = question.lower()
    name = student["student_name"]
    if any(k in q for k in ["attendance", "హాజరు", "హాజరు", "present"]):
        a = student["attendance"]
        return f"{name}'s current attendance is {a['percentage']}%. {a['attended']} out of {a['held']} sessions were attended."
    if any(k in q for k in ["coding", "code", "program"]):
        c = student["coding"]
        trend = "improved" if c["score"] > c["previous_week_score"] else "has not improved"
        weak = ", ".join(c["weak_topics"])
        return f"{name}'s coding score is {c['score']}%, with {c['completed']} of {c['assigned']} assigned problems completed. The score {trend} from {c['previous_week_score']}% last week. The main areas to improve are {weak}."
    if any(k in q for k in ["college", "campus", "come today", "came today", "వచ్చ", "today"]):
        cp = student["campus"]
        if cp["present_today"]:
            return f"Yes. {name} is recorded as present on campus today and entered at {cp['entry_time']}."
        return f"No campus entry is recorded for {name} today."
    return (
        f"{name}'s attendance is {student['attendance']['percentage']}%, training attendance is "
        f"{student['training']['percentage']}%, and coding score is {student['coding']['score']}%. "
        f"{student['coding']['completed']} of {student['coding']['assigned']} coding problems are complete."
    )

def explain(student: dict, question: str, language: str = "auto"):
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return fallback_explanation(student, question), "fallback"

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        prompt = f"""
PARENT_LANGUAGE: {language}
PARENT_QUESTION: {question}

STUDENT_DATA:
{json.dumps(student, ensure_ascii=False)}

Give only the response that should be spoken to the parent.
"""
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config={"system_instruction": SYSTEM_INSTRUCTION, "temperature": 0.2},
        )
        text = (response.text or "").strip()
        return (text or fallback_explanation(student, question)), "gemini"
    except Exception:
        return fallback_explanation(student, question), "fallback"
