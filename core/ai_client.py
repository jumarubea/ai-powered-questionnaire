from google import genai
from google.genai import types
from config import settings
from models import Question, QuestionType


class AIClient:
    def __init__(self):
        self.client = genai.Client(api_key=settings.MODEL_API_KEY)
        self.model = settings.MODEL

        self.context = """You are a friendly, warm questionnaire assistant. Your role is to:
1. Present questions in a conversational, approachable way
2. Thank users for their responses genuinely but briefly
3. Request clarification politely when responses are unclear
4. Keep your messages concise but friendly

Guidelines:
- Be warm but not overly enthusiastic
- Keep appreciation messages short (1 sentence max)
- When presenting questions, make them feel natural, not robotic
- For clarification, be specific about what needs to be clearer
- Never repeat the exact question text, rephrase it naturally"""

    async def _generate(self, prompt: str) -> str:
        """Generate response from the AI model."""
        full_prompt = f"{self.context}\n\n{prompt}"
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=256,
                    temperature=0.7
                )
            )
            return response.text.strip()
        except Exception as e:
            print(f"AI Error: {e}")
            # Return simple fallback
            return None

    async def present_question(self, question: Question, is_first: bool = False) -> str:
        prompt = f"""Rewrite this question in a friendly, conversational tone. Output ONLY the rephrased question, nothing else.

Original: {question.text}

Rules:
- ONE sentence only
- No greetings (no "Hi", "Hello")
- No explanations
- No follow-up questions
- Just the question itself, rephrased naturally"""

        result = await self._generate(prompt)

        # Strict cleanup
        if result:
            # Remove common AI additions
            result = result.replace("Sure!", "").replace("Of course!", "").strip()
            # Take only first sentence
            for sep in ['. ', '? ', '! ']:
                if sep in result:
                    parts = result.split(sep)
                    result = parts[0] + sep[0]
                    break
            # If still too long, use original
            if len(result) > 100:
                result = question.text

        if is_first:
            return f"Welcome! {result or question.text}"

        return result or question.text

    async def appreciate_response(self, question: Question, response_value: str) -> str:
        """Generate a friendly, personalized response based on the answer."""
        import random

        q_type = question.type
        q_text = question.text.lower()
        value = str(response_value).strip()

        # Name questions
        if "name" in q_text:
            name = self._extract_name(value)
            responses = [
                f"Nice to meet you, {name}!",
                f"{name} - that's a lovely name!",
                f"Great name, {name}!",
                f"Welcome, {name}!"
            ]
            return random.choice(responses)

        # Age questions
        if q_type == QuestionType.NUMERIC and ("age" in q_text or "old" in q_text):
            try:
                age = int(float(value))
                if age < 18:
                    return "Young and full of energy!"
                elif age < 30:
                    return "Great age to be!"
                elif age < 50:
                    return "The best years!"
                elif age < 70:
                    return "Experience is wisdom!"
                else:
                    return "Wow, respect for your wisdom!"
            except:
                pass

        # Date of birth
        if q_type == QuestionType.DATE and ("birth" in q_text or "dob" in q_text or "born" in q_text):
            return "Thanks for sharing!"

        # Gender
        if "gender" in q_text:
            return "Noted, thanks!"

        # Yes/No questions
        if q_type == QuestionType.YES_NO:
            if value.lower() in ["yes", "true"]:
                return "Alright, good to know!"
            else:
                return "Okay, noted!"

        # Interests/hobbies (checkbox)
        if q_type == QuestionType.CHECKBOX:
            if isinstance(response_value, list) and len(response_value) > 0:
                return f"Nice choices!"
            return "Got it!"

        # Default friendly responses
        responses = ["Got it!", "Thanks!", "Alright!", "Noted!", "Cool!"]
        return random.choice(responses)

    def _extract_name(self, value: str) -> str:
        """Extract first name from response for personalization."""
        # Just take the first word as the name
        parts = value.strip().split()
        if parts:
            return parts[0].capitalize()
        return value.capitalize()

    async def request_clarification(self, question: Question, unclear_response: str) -> str:
        prompt = f"""The user's response wasn't clear enough. Politely ask for clarification.

Original question: {question.text}
Question type: {question.type.value}
{f"Expected options: {', '.join(question.options)}" if question.options else ""}
{f"Expected range: {question.min_value} to {question.max_value}" if question.min_value is not None else ""}
User's unclear response: {unclear_response}

Be specific about what format or information you need. Keep it friendly and brief (1-2 sentences)."""

        result = await self._generate(prompt)
        return result or "Could you please clarify your answer?"

    async def completion_message(self) -> str:
        prompt = """The user has completed all questions in the questionnaire. Provide a brief, warm thank you message acknowledging their time and letting them know their responses have been recorded. Keep it to 2 sentences maximum."""

        result = await self._generate(prompt)
        return result or "Thank you for completing the questionnaire! Your responses have been saved."

    def validate_response(self, question: Question, value: str | list | int | float | bool) -> tuple[bool, str]:
        """Validate response based on question type. Returns (is_valid, error_message)."""
        if question.required and (value is None or value == "" or value == []):
            return False, "This question requires an answer."

        if not question.required and (value is None or value == "" or value == []):
            return True, ""

        match question.type:
            case QuestionType.NUMERIC:
                try:
                    num_val = float(value)
                    if num_val < 0:
                        return False, "Please enter a positive number"
                    if question.min_value is not None and num_val < question.min_value:
                        return False, f"Value must be at least {question.min_value}"
                    if question.max_value is not None and num_val > question.max_value:
                        return False, f"Value must be at most {question.max_value}"
                except (ValueError, TypeError):
                    return False, "Please enter a valid number"

            case QuestionType.RADIO:
                if question.options and value not in question.options:
                    if not question.allow_other:
                        return False, f"Please select one of: {', '.join(question.options)}"

            case QuestionType.CHECKBOX:
                if isinstance(value, list):
                    if question.options and not question.allow_other:
                        invalid = [v for v in value if v not in question.options]
                        if invalid:
                            return False, f"Invalid options: {', '.join(invalid)}"
                else:
                    return False, "Please select options from the list"

            case QuestionType.YES_NO:
                if str(value).lower() not in ["yes", "no", "true", "false", "1", "0"]:
                    return False, "Please answer Yes or No"

            case QuestionType.DATE:
                import re
                from datetime import datetime, date
                if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(value)):
                    return False, "Please enter a valid date (YYYY-MM-DD)"
                # Check if DOB is in the past
                q_text = question.text.lower()
                if "birth" in q_text or "dob" in q_text or "born" in q_text:
                    try:
                        entered_date = datetime.strptime(str(value), "%Y-%m-%d").date()
                        if entered_date >= date.today():
                            return False, "Date of birth must be in the past"
                    except ValueError:
                        return False, "Invalid date"

            case QuestionType.TEXT:
                if not isinstance(value, str) or len(str(value).strip()) == 0:
                    if question.required:
                        return False, "Please provide a text response"

        return True, ""

