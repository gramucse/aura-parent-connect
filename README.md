# AURA Parent Connect v2.1

## What is new
- Student Management page
- Search students
- Add and edit students
- Downloadable CSV template
- Bulk CSV upload
- Insert/update based on student_id
- Validation report
- PostgreSQL ready
- Existing Retell + Gemini tools preserved
- Mentor dashboard and callbacks preserved

## Local run
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m uvicorn app.main:app --reload
```

Open:
- Docs: http://127.0.0.1:8000/docs
- Dashboard: http://127.0.0.1:8000/dashboard?admin_key=YOUR_ADMIN_KEY
- Students: http://127.0.0.1:8000/students?admin_key=YOUR_ADMIN_KEY

## Render
Build:
```bash
pip install -r requirements.txt
```

Start:
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Environment:
```text
APP_NAME=Aditya University Parent Connect
GEMINI_API_KEY=<your key>
GEMINI_MODEL=gemini-2.5-flash
AURA_TOOL_API_KEY=<your Retell tool secret>
ADMIN_KEY=<your admin secret>
DATABASE_URL=sqlite:///./aura_parent_connect_v2_1.db
```

For PostgreSQL:
```text
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME
```

## CSV Upload
1. Open `/students?admin_key=YOUR_ADMIN_KEY`
2. Download CSV Template
3. Open it in Excel
4. Keep column names unchanged
5. Add one student per row
6. Save as CSV UTF-8
7. Upload it
8. Review Inserted / Updated / Rejected counts

Strong and weak topics use `|`:
```text
Arrays|Strings|Hashing
Dynamic Programming|Graphs
```

## Important
For a real pilot, use PostgreSQL. SQLite on a normal Render web-service filesystem should be treated as demo storage.
