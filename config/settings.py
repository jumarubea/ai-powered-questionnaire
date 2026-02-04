import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    BASE_DIR: Path = Path(__file__).resolve().parent.parent

    # AI Model
    MODEL: str = os.getenv("MODEL", "")
    MODEL_API_KEY: str = os.getenv("MODEL_API_KEY", "")

    # Google Sheets
    GOOGLE_SHEET_ID: str = os.getenv("GOOGLE_SHEET_ID", "")
    GOOGLE_CREDENTIALS_FILE: str = os.getenv(
        "GOOGLE_CREDENTIALS_FILE",
        str(BASE_DIR / "credentials.json")
    )

    # Question source: "json", "sheets", or "both"
    QUESTION_SOURCE: str = os.getenv("QUESTION_SOURCE", "json")
    QUESTIONS_JSON_FILE: str = os.getenv(
        "QUESTIONS_JSON_FILE",
        str(BASE_DIR / "questions.json")
    )

    # Single sheet name (Column A = Questions, Column B = Responses)
    SHEET_NAME: str = os.getenv("SHEET_NAME", "Sheet1")

settings = Settings()
