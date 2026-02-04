import re
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path
from config import settings
from models import Question, QuestionType


class GoogleSheetsStorage:
    """Google Sheets storage for questions and responses."""

    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    def __init__(self):
        self.client: gspread.Client | None = None
        self.spreadsheet: gspread.Spreadsheet | None = None
        self.worksheet: gspread.Worksheet | None = None
        self._connect()

    def _connect(self) -> None:
        """Connect to Google Sheets using service account credentials."""
        creds_path = Path(settings.GOOGLE_CREDENTIALS_FILE)

        if not creds_path.exists():
            raise FileNotFoundError(
                f"Google credentials file not found at {creds_path}."
            )

        if not settings.GOOGLE_SHEET_ID:
            raise ValueError("GOOGLE_SHEET_ID not set in environment.")

        credentials = Credentials.from_service_account_file(
            str(creds_path),
            scopes=self.SCOPES
        )

        self.client = gspread.authorize(credentials)
        self.spreadsheet = self.client.open_by_key(settings.GOOGLE_SHEET_ID)
        self.worksheet = self.spreadsheet.sheet1

    def load_questions(self) -> list[Question]:
        """Load questions from Column A of the sheet."""
        if not self.worksheet:
            return []

        # Get all values from column A
        all_values = self.worksheet.get_all_values()
        if not all_values:
            return []

        questions = []
        # Skip header if present
        start = 1 if all_values[0][0].lower() in ["question", "questions"] else 0

        for idx, row in enumerate(all_values[start:], start=1):
            if not row or not row[0].strip():
                continue

            raw_text = row[0].strip()
            q_type, options, clean_text = self._parse_question(raw_text)

            questions.append(Question(
                id=f"q{idx}",
                text=clean_text,
                type=q_type,
                required=True,
                options=options
            ))

        return questions

    def _parse_question(self, text: str) -> tuple[QuestionType, list[str] | None, str]:
        """Parse question text to extract type, options, and clean text."""
        text_lower = text.lower()
        options = None
        q_type = QuestionType.TEXT

        # 1. Check for explicit type markers
        if "[checkbox]" in text_lower or "[multi]" in text_lower:
            q_type = QuestionType.CHECKBOX
            text = re.sub(r'\[checkbox\]|\[multi\]', '', text, flags=re.IGNORECASE).strip()
        elif "[radio]" in text_lower or "[select]" in text_lower:
            q_type = QuestionType.RADIO
            text = re.sub(r'\[radio\]|\[select\]', '', text, flags=re.IGNORECASE).strip()
        elif "[yes/no]" in text_lower or "[yesno]" in text_lower:
            q_type = QuestionType.YES_NO
            text = re.sub(r'\[yes/?no\]|\[yesno\]', '', text, flags=re.IGNORECASE).strip()
        elif "[date]" in text_lower:
            q_type = QuestionType.DATE
            text = re.sub(r'\[date\]', '', text, flags=re.IGNORECASE).strip()
        elif "[number]" in text_lower or "[numeric]" in text_lower:
            q_type = QuestionType.NUMERIC
            text = re.sub(r'\[number\]|\[numeric\]', '', text, flags=re.IGNORECASE).strip()

        # 2. Extract options from parentheses: (Option1, Option2, Option3)
        paren_match = re.search(r'\(([^)]+)\)', text)
        if paren_match:
            options_str = paren_match.group(1)
            options = [opt.strip() for opt in options_str.split(',') if opt.strip()]
            # Remove options from display text
            text = re.sub(r'\s*\([^)]+\)', '', text).strip()
            # If no explicit type but has options, default to radio
            if q_type == QuestionType.TEXT and options:
                q_type = QuestionType.RADIO

        # 3. Auto-detect from patterns (if no explicit marker)
        if q_type == QuestionType.TEXT:
            text_check = text.lower()
            if "how old" in text_check or "your age" in text_check:
                q_type = QuestionType.NUMERIC
            elif "date of birth" in text_check or "dob" in text_check or "birthday" in text_check:
                q_type = QuestionType.DATE
            elif text_check.startswith(("are you", "do you", "have you", "will you", "can you")):
                q_type = QuestionType.YES_NO

        return q_type, options, text

    def _get_next_column(self) -> str:
        """Find the next available column for responses."""
        if not self.worksheet:
            return "B"

        # Get first row to check how many columns have data
        first_row = self.worksheet.row_values(1)
        # Next column is after the last filled column (Column A has questions)
        next_col_index = len(first_row) + 1 if first_row else 2
        # Convert to column letter (1=A, 2=B, etc.)
        return self._col_index_to_letter(next_col_index)

    def _col_index_to_letter(self, index: int) -> str:
        """Convert column index (1-based) to letter (A, B, ..., Z, AA, AB, ...)."""
        result = ""
        while index > 0:
            index -= 1
            result = chr(65 + (index % 26)) + result
            index //= 26
        return result

    def save_responses(
        self,
        questions: list[str],
        responses: list[str],
        session_id: str | None = None
    ) -> bool:
        """Save responses to the next available column with session header.

        Each user session gets its own column:
        - Column A: Questions
        - Column B, C, D, ...: Responses per session with timestamp header
        """
        if not self.worksheet:
            return False

        try:
            all_values = self.worksheet.get_all_values()
            has_header = all_values and all_values[0][0].lower() in ["question", "questions"]
            start_row = 2 if has_header else 1

            # Find the next available column
            column = self._get_next_column()

            # Create header with timestamp and short session ID
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            short_id = session_id[:8] if session_id else "unknown"
            header = f"{timestamp} ({short_id})"

            updates = []

            # Add header in row 1 if we have a header row
            if has_header:
                updates.append({"range": f"{column}1", "values": [[header]]})

            # Add responses
            for idx, response in enumerate(responses):
                row_num = start_row + idx
                if isinstance(response, list):
                    response = ", ".join(str(r) for r in response)
                updates.append({"range": f"{column}{row_num}", "values": [[str(response)]]})

            if updates:
                self.worksheet.batch_update(updates)

            return True

        except Exception as e:
            print(f"Error saving to Google Sheets: {e}")
            return False

    def is_connected(self) -> bool:
        return self.client is not None and self.worksheet is not None
