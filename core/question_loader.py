import json
from pathlib import Path
from config import settings
from models import Question


class QuestionLoader:
    def __init__(self):
        self.questions: list[Question] = []

    def load(self) -> list[Question]:
        """Load questions based on configured source."""
        source = settings.QUESTION_SOURCE.lower()

        if source == "json":
            self.questions = self._load_from_json()
        elif source == "sheets":
            self.questions = self._load_from_sheets()
        elif source == "both":
            # Prefer JSON, fall back to sheets
            self.questions = self._load_from_json()
            if not self.questions:
                self.questions = self._load_from_sheets()
        else:
            self.questions = self._load_from_json()

        return self.questions

    def _load_from_json(self) -> list[Question]:
        """Load questions from JSON file."""
        json_path = Path(settings.QUESTIONS_JSON_FILE)
        if not json_path.exists():
            return []

        with open(json_path, "r") as f:
            data = json.load(f)

        questions = []
        for q in data.get("questions", []):
            questions.append(Question(**q))

        return questions

    def _load_from_sheets(self) -> list[Question]:
        """Load questions from Google Sheets."""
        from storage.google_sheets import GoogleSheetsStorage

        try:
            sheets = GoogleSheetsStorage()
            return sheets.load_questions()
        except Exception as e:
            print(f"Failed to load questions from Sheets: {e}")
            return []

    def get_question(self, index: int) -> Question | None:
        """Get question by index."""
        if 0 <= index < len(self.questions):
            return self.questions[index]
        return None

    def get_question_by_id(self, question_id: str) -> Question | None:
        """Get question by ID."""
        for q in self.questions:
            if q.id == question_id:
                return q
        return None

    @property
    def total_questions(self) -> int:
        return len(self.questions)
