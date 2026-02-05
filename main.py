from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Any

from core import Questionnaire
from storage import GoogleSheetsStorage
from config import settings


questionnaire = Questionnaire()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    questionnaire.initialize()
    yield
    # Shutdown
    pass


app = FastAPI(
    title="AI Questionnaire",
    description="Friendly AI-powered questionnaire",
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class StartResponse(BaseModel):
    session_id: str
    message: str
    question: dict | None
    is_complete: bool


class ResponseRequest(BaseModel):
    session_id: str
    value: Any


class AnswerResponse(BaseModel):
    message: str
    question: dict | None
    is_complete: bool
    needs_clarification: bool


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the questionnaire UI."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": "ai-questionnaire"}


@app.post("/api/start", response_model=StartResponse)
async def start_questionnaire():
    """Start a new questionnaire session."""
    session_id = questionnaire.create_session()
    ai_response = await questionnaire.start_session(session_id)

    return StartResponse(
        session_id=session_id,
        message=ai_response.message,
        question=ai_response.question.model_dump() if ai_response.question else None,
        is_complete=ai_response.is_complete
    )


@app.post("/api/respond", response_model=AnswerResponse)
async def submit_response(request: ResponseRequest):
    """Submit a response and get the next question."""
    session = questionnaire.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    ai_response = await questionnaire.process_response(
        request.session_id,
        request.value
    )

    # If completed, save to Google Sheets
    if ai_response.is_complete and not ai_response.needs_clarification:
        try:
            sheets = GoogleSheetsStorage()
            questions = questionnaire.get_questions_for_sheet_header()
            values = questionnaire.get_responses_for_sheet_row(request.session_id)
            sheets.save_responses(questions, values, session_id=request.session_id)
        except Exception as e:
            print(f"Warning: Could not save to Google Sheets: {e}")

    return AnswerResponse(
        message=ai_response.message,
        question=ai_response.question.model_dump() if ai_response.question else None,
        is_complete=ai_response.is_complete,
        needs_clarification=ai_response.needs_clarification
    )


@app.get("/api/status/{session_id}")
async def get_status(session_id: str):
    """Get session status."""
    session = questionnaire.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_id,
        "current_question": session.current_question_index,
        "total_questions": questionnaire.question_loader.total_questions,
        "completed": session.completed,
        "response_count": len(session.responses)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
