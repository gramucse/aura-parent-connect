
import os, json
from dotenv import load_dotenv
load_dotenv()

SYSTEM_INSTRUCTION = """
You are AURA Parent Connect for Aditya University.
STUDENT_DATA is the only source of truth.
Never invent student facts.
Keep answers to 2-4 spoken sentences.
In Telugu, use natural spoken Telugu and keep common technical terms in English when natural.
Say percentages explicitly.
Never mention implementation details.
"""

def fallback(student, question, language="auto"):
    name=student["student_name"]; a=student["attendance"]; c=student["coding"]; cp=student["campus"]
    is_te=str(language).lower() in {"te","telugu"}
    q=question.lower()
    if "attendance" in q:
        return (f"{name} attendance ప్రస్తుతం {a['percentage']} శాతం ఉంది. మొత్తం {a['held']} sessions‌లో {a['attended']} attend అయ్యాడు."
                if is_te else f"{name}'s attendance is {a['percentage']} percent. {a['attended']} out of {a['held']} sessions were attended.")
    if "coding" in q or "code" in q:
        weak=", ".join(c["weak_topics"])
        return (f"{name} coding score ప్రస్తుతం {c['score']} శాతం ఉంది. ఇచ్చిన {c['assigned']} coding problems‌లో {c['completed']} పూర్తి చేశాడు. {weak} పై ఇంకా practice అవసరం ఉంది."
                if is_te else f"{name}'s coding score is {c['score']} percent. {c['completed']} of {c['assigned']} coding problems are complete. Focus more on {weak}.")
    if any(k in q for k in ["campus","college","today"]):
        if cp["present_today"]:
            return (f"అవును. {name} ఈరోజు college‌కు వచ్చాడు. ఉదయం {cp['entry_time']}కి campus entry నమోదైంది."
                    if is_te else f"Yes. {name} is recorded as present today and entered campus at {cp['entry_time']}.")
    return f"{name}'s attendance is {a['percentage']} percent and coding score is {c['score']} percent."

def explain(student, question, language="auto"):
    key=os.getenv("GEMINI_API_KEY","").strip()
    if not key: return fallback(student,question,language),"fallback"
    try:
        from google import genai
        client=genai.Client(api_key=key)
        model=os.getenv("GEMINI_MODEL","gemini-2.5-flash")
        response=client.models.generate_content(
            model=model,
            contents=f"PARENT_LANGUAGE: {language}\nPARENT_QUESTION: {question}\nSTUDENT_DATA:\n{json.dumps(student,ensure_ascii=False)}\nReturn only the spoken answer.",
            config={"system_instruction":SYSTEM_INSTRUCTION,"temperature":0.2},
        )
        text=(response.text or "").strip()
        return (text or fallback(student,question,language)),"gemini"
    except Exception:
        return fallback(student,question,language),"fallback"
