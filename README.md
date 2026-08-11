# AURA Parent Connect — Demo v0.1

A working backend starter for a multilingual AI parent voice agent.

## Demo scope

- Parent verification
- Attendance
- Coding score
- Problems completed
- Coding trend / weak areas
- Training attendance
- Campus presence and entry time
- AI-generated parent-friendly explanation
- Mentor callback request
- English + Telugu prompt design (Hindi-ready)

## Architecture

Parent Phone
→ Retell Voice Agent
→ AURA FastAPI tools
→ Demo student data
→ Gemini Flash for concise explanation
→ Voice response

**Important:** student data comes from the database/API. Gemini only explains the data.

## 1. Run locally

Python 3.11+ recommended.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env
# macOS/Linux: cp .env.example .env

uvicorn app.main:app --reload
```

Open:

- API docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`

The demo still works without a Gemini key using deterministic fallback responses.

## 2. Add Gemini

Create a Gemini API key in Google AI Studio and put it in `.env`:

```env
GEMINI_API_KEY=your_key
GEMINI_MODEL=gemini-2.5-flash
```

Restart the server.

## 3. Test sample student

Use student:

- ID: `23A91A0501`
- registered parent mobile ends in: `4582`

Verification:

```bash
curl -X POST http://127.0.0.1:8000/verify-parent ^
  -H "Content-Type: application/json" ^
  -d "{\"student_id\":\"23A91A0501\",\"parent_mobile_last4\":\"4582\"}"
```

Explain:

```bash
curl -X POST http://127.0.0.1:8000/student/explain ^
  -H "Content-Type: application/json" ^
  -d "{\"student_id\":\"23A91A0501\",\"question\":\"How is my son's coding?\",\"language\":\"en\"}"
```

## 4. Expose backend over HTTPS

Retell must be able to call your backend.

For a quick demo, deploy to Cloud Run / Render / Railway or use a secure HTTPS tunnel.

Set a strong value in `.env`:

```env
AURA_TOOL_API_KEY=a-long-random-demo-secret
```

## 5. Configure Retell

1. Create a voice agent.
2. Paste `retell/AGENT_PROMPT.txt` as the agent prompt.
3. Add the 4 custom functions described in `retell/TOOLS.md`.
4. Add `X-AURA-API-Key` to each function.
5. Bind the agent to an inbound number or use Retell's web-call test first.
6. Call and test:
   - "How is my son's performance?"
   - "How is his coding?"
   - "Did he come to college today?"
   - "Please ask his mentor to call me."

Retell supports custom functions that call external APIs during a conversation. Its inbound-call flow can bind a voice agent to a number, and `{{user_number}}` can represent the caller number.

## 6. Demo data

Edit `data/students.json`.

For the chairman demo, use fictional/demo records unless you have formal approval to use real student/parent data.

## 7. Production upgrades

Before real parent deployment:

- Replace JSON with PostgreSQL / university API gateway
- Strong authentication / OTP for sensitive information
- Encrypt data in transit and at rest
- Role/access controls
- Audit logs
- Consent and privacy notice
- Retention policy for transcripts/recordings
- API rate limiting
- Webhook signature verification
- Proper Indian telephony/SIP integration
- Human escalation
- Monitoring and failure alerts
- Separate factual APIs from AI-generated explanations

## API rule

**AURA/Gemini may explain a fact, but may never manufacture a student fact.**
