import uuid
from datetime import datetime
from models import Question, SessionState, UserResponse, AIMessage
from .ai_client import AIClient
from .question_loader import QuestionLoader


class Questionnaire:
    def __init__(self):
        self.ai_client = AIClient()
        self.question_loader = QuestionLoader()
        self.sessions: dict[str, SessionState] = {}

    def initialize(self) -> None:
        """Load questions on startup."""
        self.question_loader.load()

    def create_session(self) -> str:
        """Create a new questionnaire session."""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = SessionState(session_id=session_id)
        return session_id

    def get_session(self, session_id: str) -> SessionState | None:
        """Get session state by ID."""
        return self.sessions.get(session_id)

    async def start_session(self, session_id: str) -> AIMessage:
        """Start a session and present the first question."""
        session = self.get_session(session_id)
        if not session:
            raise ValueError("Session not found")

        question = self.question_loader.get_question(0)
        if not question:
            return AIMessage(
                message="No questions configured. Please add questions to start.",
                is_complete=True
            )

        friendly_message = await self.ai_client.present_question(question, is_first=True)

        return AIMessage(
            message=friendly_message,
            question=question,
            is_complete=False
        )

    async def process_response(self, session_id: str, value: any) -> AIMessage:
        """Process user response and return next question or completion."""
        session = self.get_session(session_id)
        if not session:
            raise ValueError("Session not found")

        current_question = self.question_loader.get_question(session.current_question_index)
        if not current_question:
            return AIMessage(message="No current question", is_complete=True)

        # Validate the response
        is_valid, error_msg = self.ai_client.validate_response(current_question, value)

        if not is_valid:
            # Request clarification
            clarification = await self.ai_client.request_clarification(
                current_question, str(value)
            )
            session.awaiting_clarification = True
            return AIMessage(
                message=clarification,
                question=current_question,
                is_complete=False,
                needs_clarification=True
            )

        # Save the response
        session.responses.append(UserResponse(
            question_id=current_question.id,
            value=value,
            timestamp=datetime.now().isoformat()
        ))
        session.awaiting_clarification = False

        # Generate appreciation
        appreciation = await self.ai_client.appreciate_response(current_question, str(value))

        # Move to next question
        session.current_question_index += 1
        next_question = self.question_loader.get_question(session.current_question_index)

        if next_question:
            # Present next question
            next_message = await self.ai_client.present_question(next_question)
            return AIMessage(
                message=f"{appreciation} {next_message}",
                question=next_question,
                is_complete=False
            )
        else:
            # All questions completed
            session.completed = True
            completion = await self.ai_client.completion_message()
            return AIMessage(
                message=f"{appreciation} {completion}",
                is_complete=True
            )

    def get_all_responses(self, session_id: str) -> list[dict]:
        """Get all responses for a session with question info."""
        session = self.get_session(session_id)
        if not session:
            return []

        results = []
        for response in session.responses:
            question = self.question_loader.get_question_by_id(response.question_id)
            results.append({
                "question_id": response.question_id,
                "question_text": question.text if question else "Unknown",
                "response": response.value,
                "timestamp": response.timestamp
            })

        return results

    def get_questions_for_sheet_header(self) -> list[str]:
        """Get question texts for sheet header row."""
        return [q.text for q in self.question_loader.questions]

    def get_responses_for_sheet_row(self, session_id: str) -> list[str]:
        """Get responses in order for sheet row."""
        session = self.get_session(session_id)
        if not session:
            return []

        # Create a mapping of question_id to response value
        response_map = {r.question_id: r.value for r in session.responses}

        # Return values in question order
        row = []
        for question in self.question_loader.questions:
            value = response_map.get(question.id, "")
            # Convert lists to comma-separated string for sheets
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            row.append(str(value))

        return row
