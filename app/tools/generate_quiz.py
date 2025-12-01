"""Generate quiz tool."""

import json
import uuid
import base64
import logging

from google import genai
from google.genai import types

from ..config import settings
from ..prompts.assessor import ASSESSOR_SYSTEM_PROMPT, QUIZ_GENERATION_PROMPT
from .state import quiz_store

logger = logging.getLogger(__name__)


def generate_quiz(content: str, content_type: str = "text", num_questions: int = 5) -> str:
    """Generate a knowledge assessment quiz from learning content."""
    logger.info(f"[TOOL] generate_quiz: {content_type}, {num_questions} questions")

    client = genai.Client(api_key=settings.GOOGLE_API_KEY)

    prompt = QUIZ_GENERATION_PROMPT.format(
        content=content[:5000] if content_type == "text" else "[PDF Content]",
        num_questions_per_topic=max(1, num_questions // 3),
        total_questions=num_questions,
    )

    if content_type == "pdf":
        parts = [
            types.Part.from_bytes(data=base64.b64decode(content), mime_type="application/pdf"),
            types.Part.from_text(text=prompt),
        ]
    else:
        parts = [types.Part.from_text(text=prompt)]

    response = client.models.generate_content(
        model=settings.AI_MODEL,
        contents=types.Content(role="user", parts=parts),
        config=types.GenerateContentConfig(
            system_instruction=ASSESSOR_SYSTEM_PROMPT,
            temperature=0.3,
            response_mime_type="application/json",
            response_schema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "topics": {"type": "array", "items": {"type": "string"}},
                    "questions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "topic": {"type": "string"},
                                "question": {"type": "string"},
                                "options": {
                                    "type": "object",
                                    "properties": {
                                        "A": {"type": "string"},
                                        "B": {"type": "string"},
                                        "C": {"type": "string"},
                                        "D": {"type": "string"},
                                    },
                                    "required": ["A", "B", "C", "D"],
                                },
                                "correct_answer": {"type": "string"},
                            },
                            "required": ["id", "question", "options", "correct_answer"],
                        },
                    },
                },
                "required": ["title", "questions"],
            },
        ),
    )

    result = json.loads(response.text)
    session_id = str(uuid.uuid4())

    # Normalize correct_answer to correct for internal storage
    for q in result.get("questions", []):
        if "correct_answer" in q:
            q["correct"] = q.pop("correct_answer")

    quiz_store[session_id] = result
    logger.info(f"[TOOL] generate_quiz: Stored quiz session {session_id}, quiz_store now has {len(quiz_store)} sessions")

    # Remove correct answers from response
    questions = [{k: v for k, v in q.items() if k != "correct"} for q in result.get("questions", [])]

    return json.dumps({
        "session_id": session_id,
        "title": result.get("title", "Quiz"),
        "topics": result.get("topics", []),
        "questions": questions,
    })
