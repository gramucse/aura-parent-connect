
import os, csv, io
from fastapi import FastAPI, HTTPException, Header, Depends, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from .database import Base, engine, get_db, SessionLocal
from .db_models import Student, MentorCallback, CallLog
from .schemas import VerifyRequest, ExplainRequest, CallbackRequest, CallbackStatusRequest, RetellEnvelope
from .services import *
from .gemini_service import explain
from .seed import seed_students

app=FastAPI(title=os.getenv("APP_NAME","Aditya University Parent Connect"),version="2.1.0")
templates=Jinja2Templates(directory="templates")

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db=SessionLocal()
    try: seed_students(db)
    finally: db.close()

def require_tool_key(key):
    if key!=os.getenv("AURA_TOOL_API_KEY","change-me"):
        raise HTTPException(401,"Invalid AURA tool API key")

def require_admin_key(key):
    if key!=os.getenv("ADMIN_KEY","change-admin-key"):
        raise HTTPException(401,"Invalid admin key")

def call_id(payload):
    c=payload.call or {}
    return c.get("call_id") or c.get("id") or "web-test"

def caller(payload):
    c=payload.call or {}
    return c.get("from_number") or c.get("user_number") or c.get("caller_number")

@app.get("/")
def root():
    return {"name":os.getenv("APP_NAME","Aditya University Parent Connect"),"version":"2.1.0","status":"ready",
            "docs":"/docs","dashboard":"/dashboard","students":"/students"}

@app.get("/health")
def health(): return {"ok":True,"version":"2.1.0"}

@app.post("/verify-parent")
def api_verify(payload:VerifyRequest,db:Session=Depends(get_db)):
    ok,msg,s=verify_parent(db,payload.student_id,payload.caller_number,payload.parent_mobile_last4)
    return {"verified":ok,"message":msg,"student_id":s.student_id if s else None,"student_name":s.student_name if s else None}

@app.get("/student/{student_id}/summary")
def api_summary(student_id:str,db:Session=Depends(get_db)):
    s=get_student(db,student_id)
    if not s: raise HTTPException(404,"Student not found")
    return student_summary(s)

@app.post("/student/explain")
def api_explain(payload:ExplainRequest,db:Session=Depends(get_db)):
    s=get_student(db,payload.student_id)
    if not s: raise HTTPException(404,"Student not found")
    answer,engine_name=explain(student_summary(s),payload.question,payload.language)
    return {"answer":answer,"engine":engine_name}

@app.post("/tools/verify-parent")
def tool_verify(payload:RetellEnvelope,x_aura_api_key:str|None=Header(default=None),db:Session=Depends(get_db)):
    require_tool_key(x_aura_api_key)
    d=payload.args or {}; cid=call_id(payload); num=d.get("caller_number") or caller(payload)
    ok,msg,s=verify_parent(db,d.get("student_id"),num,d.get("parent_mobile_last4"))
    upsert_session(db,cid,num,ok,s.student_id if s else None)
    log_event(db,cid,num,s.student_id if s else d.get("student_id"),tool_name="verify_parent",success=ok,detail=msg)
    return {"verified":ok,"message":msg,"student_id":s.student_id if s else None,"student_name":s.student_name if s else None}

@app.post("/tools/student-summary")
def tool_summary(payload:RetellEnvelope,x_aura_api_key:str|None=Header(default=None),db:Session=Depends(get_db)):
    require_tool_key(x_aura_api_key); d=payload.args or {}; cid=call_id(payload)
    s=get_student(db,d.get("student_id"))
    if not s:
        log_event(db,cid,student_id=d.get("student_id"),tool_name="student_summary",success=False,detail="Student not found")
        return {"found":False,"message":"Student record not found."}
    log_event(db,cid,student_id=s.student_id,tool_name="student_summary",success=True)
    return {"found":True,"student":student_summary(s)}

@app.post("/tools/explain")
def tool_explain(payload:RetellEnvelope,x_aura_api_key:str|None=Header(default=None),db:Session=Depends(get_db)):
    require_tool_key(x_aura_api_key); d=payload.args or {}; cid=call_id(payload)
    sid=d.get("student_id"); q=d.get("question","Give an overall performance summary."); lang=d.get("language","auto")
    s=get_student(db,sid)
    if not s:
        log_event(db,cid,student_id=sid,tool_name="explain_student_performance",success=False,language=lang,detail="Student not found")
        return {"found":False,"answer":"Student record not found."}
    answer,engine_name=explain(student_summary(s),q,lang)
    upsert_session(db,cid,verified=True,student_id=s.student_id,language=lang)
    log_event(db,cid,student_id=s.student_id,tool_name="explain_student_performance",success=True,language=lang,detail=q)
    return {"found":True,"answer":answer,"engine":engine_name}

@app.post("/tools/request-callback")
def tool_callback(payload:RetellEnvelope,x_aura_api_key:str|None=Header(default=None),db:Session=Depends(get_db)):
    require_tool_key(x_aura_api_key); d=payload.args or {}; cid=call_id(payload)
    s=get_student(db,d.get("student_id")); num=d.get("caller_number") or caller(payload)
    if not s: return {"created":False,"message":"Student record not found."}
    item=create_callback(db,s,d.get("concern","Parent requested mentor callback"),num,cid)
    log_event(db,cid,num,s.student_id,tool_name="request_callback",success=True,detail=item.concern)
    return {"created":True,"message":f"Callback request created for mentor {s.mentor_name}.","callback_id":item.id,"status":item.status}

@app.get("/dashboard",response_class=HTMLResponse)
def dashboard(request:Request,admin_key:str|None=None,db:Session=Depends(get_db)):
    require_admin_key(admin_key)
    metrics=dashboard_metrics(db)
    callbacks=db.execute(select(MentorCallback).order_by(MentorCallback.created_at.desc()).limit(50)).scalars().all()
    logs=db.execute(select(CallLog).order_by(CallLog.created_at.desc()).limit(80)).scalars().all()
    return templates.TemplateResponse(request=request,name="dashboard.html",
        context={"metrics":metrics,"callbacks":callbacks,"logs":logs,"admin_key":admin_key})

@app.post("/admin/callbacks/{callback_id}/status")
def update_callback(callback_id:int,payload:CallbackStatusRequest,x_admin_key:str|None=Header(default=None),db:Session=Depends(get_db)):
    require_admin_key(x_admin_key)
    item=db.get(MentorCallback,callback_id)
    if not item: raise HTTPException(404,"Callback not found")
    if payload.status not in {"Pending","Contacted","Resolved"}: raise HTTPException(400,"Invalid status")
    item.status=payload.status; db.commit()
    return {"updated":True,"callback_id":callback_id,"status":item.status}

CSV_COLUMNS=[
"student_id","student_name","parent_name","parent_mobile","mentor_name",
"attendance_percentage","attendance_attended","attendance_held","coding_score","coding_assigned",
"coding_completed","coding_previous_week","strong_topics","weak_topics","training_percentage",
"training_attended","training_held","present_today","entry_time","previous_day_entry_time",
"campus_regularity_score"]

@app.get("/students",response_class=HTMLResponse)
def students_page(request:Request,admin_key:str|None=None,q:str|None=None,db:Session=Depends(get_db)):
    require_admin_key(admin_key)
    stmt=select(Student).order_by(Student.student_id)
    if q:
        p=f"%{q.strip()}%"
        stmt=select(Student).where(or_(Student.student_id.ilike(p),Student.student_name.ilike(p),
                                      Student.parent_name.ilike(p),Student.mentor_name.ilike(p))).order_by(Student.student_id)
    students=db.execute(stmt.limit(1000)).scalars().all()
    return templates.TemplateResponse(request=request,name="students.html",
        context={"students":students,"q":q or "","admin_key":admin_key,"message":request.query_params.get("message","")})

@app.get("/students/new",response_class=HTMLResponse)
def new_student(request:Request,admin_key:str|None=None):
    require_admin_key(admin_key)
    return templates.TemplateResponse(request=request,name="student_form.html",
        context={"student":None,"admin_key":admin_key,"mode":"new","errors":[]})

@app.get("/students/{student_id}/edit",response_class=HTMLResponse)
def edit_student(student_id:str,request:Request,admin_key:str|None=None,db:Session=Depends(get_db)):
    require_admin_key(admin_key); s=get_student(db,student_id)
    if not s: raise HTTPException(404,"Student not found")
    return templates.TemplateResponse(request=request,name="student_form.html",
        context={"student":s,"admin_key":admin_key,"mode":"edit","errors":[]})

@app.post("/students/save")
def save_student(
    admin_key:str=Form(...), student_id:str=Form(...), student_name:str=Form(...),
    parent_name:str=Form(...), parent_mobile:str=Form(...), mentor_name:str=Form(...),
    attendance_percentage:int=Form(0), attendance_attended:int=Form(0), attendance_held:int=Form(0),
    coding_score:int=Form(0), coding_assigned:int=Form(0), coding_completed:int=Form(0),
    coding_previous_week:int=Form(0), strong_topics:str=Form(""), weak_topics:str=Form(""),
    training_percentage:int=Form(0), training_attended:int=Form(0), training_held:int=Form(0),
    present_today:str|None=Form(None), entry_time:str=Form(""), previous_day_entry_time:str=Form(""),
    campus_regularity_score:int=Form(0), db:Session=Depends(get_db)
):
    require_admin_key(admin_key)
    data=locals().copy(); data.pop("db",None); data.pop("admin_key",None)
    data["strong_topics"]=[x.strip() for x in strong_topics.split("|") if x.strip()]
    data["weak_topics"]=[x.strip() for x in weak_topics.split("|") if x.strip()]
    data["present_today"]=present_today=="on"
    errors=validate_student_payload(data)
    if errors: raise HTTPException(400,"; ".join(errors))
    s,created=upsert_student(db,data); action="created" if created else "updated"
    return RedirectResponse(f"/students?admin_key={admin_key}&message={s.student_id}%20{action}%20successfully",status_code=303)

@app.get("/students/template.csv")
def download_template(admin_key:str|None=None):
    require_admin_key(admin_key)
    out=io.StringIO(); w=csv.DictWriter(out,fieldnames=CSV_COLUMNS); w.writeheader()
    w.writerow({"student_id":"23A91A0501","student_name":"Rahul Kumar","parent_name":"Suresh Kumar",
        "parent_mobile":"+919876544582","mentor_name":"M. Ashok","attendance_percentage":"91",
        "attendance_attended":"109","attendance_held":"120","coding_score":"76","coding_assigned":"50",
        "coding_completed":"38","coding_previous_week":"68","strong_topics":"Arrays|Strings",
        "weak_topics":"Dynamic Programming|Graphs","training_percentage":"94","training_attended":"47",
        "training_held":"50","present_today":"true","entry_time":"09:12 AM",
        "previous_day_entry_time":"09:26 AM","campus_regularity_score":"95"})
    return StreamingResponse(iter([out.getvalue()]),media_type="text/csv",
        headers={"Content-Disposition":"attachment; filename=AURA_Student_Upload_Template.csv"})

@app.post("/students/upload",response_class=HTMLResponse)
async def upload_csv(request:Request,admin_key:str=Form(...),file:UploadFile=File(...),db:Session=Depends(get_db)):
    require_admin_key(admin_key)
    inserted=updated=rejected=0; errors=[]
    if not file.filename.lower().endswith(".csv"):
        errors=["Only CSV files are accepted."]; rejected=1
    else:
        try: text=(await file.read()).decode("utf-8-sig")
        except UnicodeDecodeError:
            text=""; errors=["CSV must be saved as UTF-8."]; rejected=1
        if not errors:
            reader=csv.DictReader(io.StringIO(text))
            missing=[c for c in CSV_COLUMNS if c not in (reader.fieldnames or [])]
            if missing:
                errors=[f"Missing columns: {', '.join(missing)}"]; rejected=1
            else:
                for n,row in enumerate(reader,start=2):
                    data=dict(row)
                    data["strong_topics"]=[x.strip() for x in (row.get("strong_topics") or "").split("|") if x.strip()]
                    data["weak_topics"]=[x.strip() for x in (row.get("weak_topics") or "").split("|") if x.strip()]
                    er=validate_student_payload(data)
                    if er:
                        rejected+=1; errors.append(f"Row {n}: "+"; ".join(er)); continue
                    try:
                        _,created=upsert_student(db,data)
                        inserted+=1 if created else 0; updated+=0 if created else 1
                    except Exception:
                        db.rollback(); rejected+=1; errors.append(f"Row {n}: database error")
    return templates.TemplateResponse(request=request,name="upload_result.html",
        context={"admin_key":admin_key,"inserted":inserted,"updated":updated,"rejected":rejected,"errors":errors[:100]})

@app.get("/admin/students")
def admin_students(x_admin_key:str|None=Header(default=None),q:str|None=None,db:Session=Depends(get_db)):
    require_admin_key(x_admin_key)
    stmt=select(Student).order_by(Student.student_id)
    if q:
        p=f"%{q.strip()}%"
        stmt=select(Student).where(or_(Student.student_id.ilike(p),Student.student_name.ilike(p),Student.parent_name.ilike(p)))
    rows=db.execute(stmt.limit(1000)).scalars().all()
    return {"count":len(rows),"students":[{"student_id":s.student_id,"student_name":s.student_name,
        "parent_name":s.parent_name,"parent_mobile":s.parent_mobile,"mentor_name":s.mentor_name,
        "attendance_percentage":s.attendance_percentage,"coding_score":s.coding_score,
        "training_percentage":s.training_percentage,"present_today":s.present_today} for s in rows]}
