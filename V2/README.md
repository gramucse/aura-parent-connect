# AURA Parent Connect v2

Version 2 upgrades the working Retell + Gemini demo into a stronger pilot-ready application.

## New in v2

- Retell envelope-compatible tools
- Gemini-backed parent-friendly explanations
- Natural Telugu guidance
- SQLAlchemy database layer
- SQLite by default, PostgreSQL-ready through `DATABASE_URL`
- Persistent parent sessions per `call_id`
- Mentor callback management
- Call/tool event logging
- Mentor/admin dashboard
- Generic Retell webhook logging
- Separate tool and admin keys
- Demo student seeding
- Direct Swagger testing endpoints

## Architecture

Parent
→ Retell voice agent
→ AURA FastAPI v2
→ Parent/session verification
→ Student DB / future university APIs
→ Gemini
→ voice response

Mentor callback
→ PostgreSQL/SQLite
→ dashboard

## Run locally

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate

pip install -r requirements.txt
copy .env.example .env

python -m uvicorn app.main:app --reload
```

Open:
- Docs: http://127.0.0.1:8000/docs
- Dashboard: http://127.0.0.1:8000/dashboard?admin_key=admin-demo-key

## Render deployment

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Environment variables:

```text
APP_NAME=Aditya University Parent Connect
GEMINI_API_KEY=<your key>
GEMINI_MODEL=gemini-2.5-flash
AURA_TOOL_API_KEY=<new secret>
DATABASE_URL=sqlite:///./aura_parent_connect_v2.db
ADMIN_KEY=<new admin secret>
```

For a real pilot, attach a managed PostgreSQL database and replace `DATABASE_URL`.

## PostgreSQL example

```text
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME
```

## Retell

Paste `retell/AGENT_PROMPT_V2.txt` into the agent prompt.

Configure the four functions from `retell/TOOLS_V2.md`.

## Demo record

Student ID: `23A91A0501`
Parent mobile last 4: `4582`

## Dashboard

Open:

```text
https://YOUR-APP.onrender.com/dashboard?admin_key=YOUR_ADMIN_KEY
```

The dashboard shows:
- total sessions
- verified sessions
- tool events
- pending callbacks
- callback list
- recent call/tool activity

## Before production

- Use PostgreSQL
- Add OTP for sensitive information
- Verify Retell webhook signatures
- Add proper authorization/roles for dashboard
- Encrypt and minimize PII
- Define transcript/recording retention
- Connect university APIs instead of demo tables
- Load-test concurrent calls
- Add monitoring and alerting
