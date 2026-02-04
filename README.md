# AI-Powered Questionnaire

A friendly, AI-powered questionnaire with a chat-like interface. The AI presents questions conversationally, appreciates responses, requests clarification when needed, and stores all responses in Google Sheets.

## Features

- **Conversational AI**: Questions presented in a friendly, natural way
- **Multiple Input Types**: Text, numeric, date, radio, checkbox, yes/no
- **Smart Validation**: AI requests clarification for unclear responses
- **Google Sheets Integration**: Responses saved automatically
- **Flexible Question Management**: Load from JSON or Google Sheets

## Quick Start

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Required:
- `MODEL_API_KEY`: Your Google AI API key

### 3. Run the Server

```bash
uv run uvicorn main:app --reload
```

Open http://localhost:8000 in your browser.

## Google Sheets Setup (Optional)

To save responses to Google Sheets:

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the Google Sheets API

### 2. Create Service Account

1. Go to IAM & Admin → Service Accounts
2. Create a service account
3. Download the JSON key file
4. Save it as `credentials.json` in the project root

### 3. Share Your Sheet

1. Create a new Google Sheet
2. Share it with the service account email (found in credentials.json)
3. Copy the Sheet ID from the URL and add to `.env`

## Customizing Questions

### Option 1: Google Sheets (Recommended)

Set `QUESTION_SOURCE=sheets` in `.env`. Your sheet should have:
- **Column A**: Questions
- **Column B**: Responses (filled automatically)

#### Question Format in Column A

Write questions naturally. The system auto-detects question types:

| Question Example | Detected Type |
|------------------|---------------|
| `What is your name?` | Text |
| `How old are you?` | Numeric |
| `What is your date of birth?` | Date |
| `Are you employed?` | Yes/No |
| `Gender (Male, Female, Other)` | Radio |
| `[checkbox] Interests (Tech, Sports, Music)` | Checkbox |

**Type Markers** (optional, for explicit control):
- `[checkbox]` - Multiple selection
- `[radio]` or `[select]` - Single selection
- `[yes/no]` - Yes/No toggle
- `[date]` - Date picker
- `[number]` - Numeric input

**Options Format:**
- In parentheses: `Favorite color (Red, Blue, Green)`
- After colon: `Select size: Small, Medium, Large`

### Option 2: JSON File

Set `QUESTION_SOURCE=json` and edit `questions.json`:

```json
{
  "questions": [
    {
      "id": "q1",
      "text": "What is your name?",
      "type": "text",
      "required": true
    }
  ]
}
```

### Question Types

| Type | Description |
|------|-------------|
| `text` | Free-form text input |
| `numeric` | Number input (age, quantity) |
| `date` | Date picker |
| `radio` | Single selection from options |
| `checkbox` | Multiple selection |
| `yes_no` | Yes/No toggle |

## Project Structure

```
ai-based-form/
├── main.py              # FastAPI application
├── config/              # Configuration
├── core/                # Business logic
│   ├── ai_client.py     # AI interactions
│   ├── questionnaire.py # Flow control
│   └── question_loader.py
├── storage/             # Google Sheets
├── models/              # Data schemas
├── static/              # CSS & JS
├── templates/           # HTML
└── questions.json       # Question config
```

## License

MIT
