# Retell custom functions for v2

Use the same header for every tool:

`X-AURA-API-Key: <AURA_TOOL_API_KEY from Render>`

All Retell tools POST the Retell envelope (`call`, `name`, `args`) to AURA.

## verify_parent
POST `/tools/verify-parent`

Args:
- `student_id` required string
- `caller_number` optional string (use `{{user_number}}` when available)
- `parent_mobile_last4` optional string

## student_summary
POST `/tools/student-summary`

Args:
- `student_id` required string

## explain_student_performance
POST `/tools/explain`

Args:
- `student_id` required string
- `question` required string
- `language` optional string (`en`, `te`, or `auto`)

## request_callback
POST `/tools/request-callback`

Args:
- `student_id` required string
- `concern` required string
- `caller_number` optional string
