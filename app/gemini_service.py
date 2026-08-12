\
import os, json
from dotenv import load_dotenv

load_dotenv()

SYSTEM_INSTRUCTION = """
You are AURA Parent Connect for Aditya University.

STRICT RULES:
- STUDENT_DATA is the only source of truth.
- Never invent student facts.
- Keep spoken answers short, normally 2 to 4 sentences.
- Reply in the parent's requested language.
- In English, always say scores/attendance as percentages when the field represents a percentage.
- In Telugu, use natural spoken Telugu. Keep common technical words such as attendance, coding, score, campus,
  Dynamic Programming, Graphs, Arrays and Strings in English when that sounds more natural.
- Avoid awkward literal Telugu translations.
- Prefer "coding problems" over "tasks".
- Do not mention internal JSON, tools, Gemini, APIs, or implementation details.
- If data is absent, clearly say it is currently unavailable.
"""

def fallback_explanation(student: dict, question: str, language: str = "auto"):
    q = question.lower()
    name = student["student_name"]
    a = student["attendance"]
    c = student["coding"]
    t = student["training"]
    cp = student["campus"]

    is_te = language.lower() in {"te", "telugu"}

    if any(k in q for k in ["attendance", "హాజరు"]):
        if is_te:
            return f"{name} attendance ప్రస్తుతం {a['percentage']} శాతం ఉంది. మొత్తం {a['held']} sessions‌లో {a['attended']} attend అయ్యాడు."
        return f"{name}'s current attendance is {a['percentage']} percent. {a['attended']} out of {a['held']} sessions were attended."

    if any(k in q for k in ["coding", "code", "program"]):
        weak = ", ".join(c["weak_topics"])
        if is_te:
            return f"{name} coding score ప్రస్తుతం {c['score']} శాతం ఉంది. ఇచ్చిన {c['assigned']} coding problems‌లో {c['completed']} పూర్తి చేశాడు. {weak} పై ఇంకా practice అవసరం ఉంది."
        return f"{name}'s coding score is {c['score']} percent. {c['completed']} of {c['assigned']} assigned coding problems are complete. The main areas to improve are {weak}."

    if any(k in q for k in ["college", "campus", "today", "వచ్చ"]):
        if cp["present_today"]:
            if is_te:
                return f"అవును. {name} ఈరోజు college‌కు వచ్చాడు. ఉదయం {cp['entry_time']}కి campus entry నమోదైంది."
            return f"Yes. {name} is recorded as present today and entered campus at {cp['entry_time']}."
        return f"No campus entry is recorded for {name} today."

    if is_te:
        return f"{name} overall performance బాగుంది. Attendance {a['percentage']} శాతం ఉంది. Coding score {c['score']} శాతం ఉంది. Training attendance {t['percentage']} శాతం ఉంది."
    return f"{name}'s attendance is {a['percentage']} percent, training attendance is {t['percentage']} percent, and coding score is {c['score']} percent."

def explain(student: dict, question: str, language: str = "auto"):
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return fallback_explanation(student, question, language), "fallback"

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        prompt = f"""
PARENT_LANGUAGE: {language}
PARENT_QUESTION: {question}

STUDENT_DATA:
{json.dumps(student, ensure_ascii=False)}

Return only the spoken answer for the parent.
"""
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config={"system_instruction": SYSTEM_INSTRUCTION, "temperature": 0.2},
        )
        text = (response.text or "").strip()
        return (text or fallback_explanation(student, question, language)), "gemini"
    except Exception:
        return fallback_explanation(student, question, language), "fallback"
