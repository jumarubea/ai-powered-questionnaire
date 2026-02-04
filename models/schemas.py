from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    TEXT = "text"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    NUMERIC = "numeric"
    DATE = "date"
    YES_NO = "yes_no"


class Question(BaseModel):
    id: str
    text: str
    type: QuestionType
    required: bool = True
    options: list[str] | None = None  # For checkbox/radio
    min_value: float | None = Field(None, alias="min")
    max_value: float | None = Field(None, alias="max")
    placeholder: str | None = None

    class Config:
        populate_by_name = True


class UserResponse(BaseModel):
    question_id: str
    value: Any
    timestamp: str | None = None


class SessionState(BaseModel):
    session_id: str
    current_question_index: int = 0
    responses: list[UserResponse] = Field(default_factory=list)
    completed: bool = False
    awaiting_clarification: bool = False


class AIMessage(BaseModel):
    message: str
    question: Question | None = None
    is_complete: bool = False
    needs_clarification: bool = False


class ResponseRequest(BaseModel):
    session_id: str
    value: Any
