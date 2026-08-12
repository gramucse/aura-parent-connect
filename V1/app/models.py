\
from pydantic import BaseModel, Field
from typing import Optional
from typing import Any

class VerifyRequest(BaseModel):
    student_id: str
    caller_number: Optional[str] = None
    parent_mobile_last4: Optional[str] = Field(default=None, min_length=4, max_length=4)

class ExplainRequest(BaseModel):
    student_id: str
    question: str
    language: str = "auto"

class CallbackRequest(BaseModel):
    student_id: str
    concern: str
    caller_number: Optional[str] = None

class RetellToolRequest(BaseModel):
    student_id: str
    caller_number: Optional[str] = None
    parent_mobile_last4: Optional[str] = None
    question: Optional[str] = None
    language: str = "auto"
    concern: Optional[str] = None


class RetellEnvelope(BaseModel):
    call: dict[str, Any] | None = None
    name: str | None = None
    args: dict[str, Any] = {}
