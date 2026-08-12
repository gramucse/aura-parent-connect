\
from pydantic import BaseModel
from typing import Any

class VerifyRequest(BaseModel):
    student_id: str
    caller_number: str | None = None
    parent_mobile_last4: str | None = None

class ExplainRequest(BaseModel):
    student_id: str
    question: str
    language: str = "auto"

class CallbackRequest(BaseModel):
    student_id: str
    concern: str
    caller_number: str | None = None
    call_id: str | None = None

class CallbackStatusRequest(BaseModel):
    status: str

class RetellEnvelope(BaseModel):
    call: dict[str, Any] | None = None
    name: str | None = None
    args: dict[str, Any] = {}
