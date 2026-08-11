# Retell Custom Functions

Set header on every custom function:

`X-AURA-API-Key: <same value as AURA_TOOL_API_KEY>`

Replace `https://YOUR-BACKEND.example.com` with your deployed HTTPS URL.

## 1. verify_parent
POST `https://YOUR-BACKEND.example.com/tools/verify-parent`

Parameters:
- `student_id` (string, required)
- `caller_number` (string, use Retell dynamic variable `{{user_number}}`)
- `parent_mobile_last4` (string, optional)

Purpose: Verify caller before student information is disclosed.

## 2. student_summary
POST `https://YOUR-BACKEND.example.com/tools/student-summary`

Parameters:
- `student_id` (string, required)

Purpose: Fetch trusted structured data.

## 3. explain_student_performance
POST `https://YOUR-BACKEND.example.com/tools/explain`

Parameters:
- `student_id` (string, required)
- `question` (string, required; the parent's current question)
- `language` (string, optional; `auto`, `te`, `en`, `hi`)

Purpose: Generate a concise parent-friendly answer using Gemini, with fallback if Gemini is unavailable.

## 4. request_callback
POST `https://YOUR-BACKEND.example.com/tools/request-callback`

Parameters:
- `student_id` (string, required)
- `concern` (string, required)
- `caller_number` (string, use `{{user_number}}`)

Purpose: Record mentor escalation.
