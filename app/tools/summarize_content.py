"""Summarize content tool."""

import json
import base64
import logging

from google import genai
from google.genai import types

from ..config import settings
from ..prompts.summarizer import SUMMARIZER_SYSTEM_PROMPT, AUDIENCE_TEMPLATES, SUMMARIZE_PROMPT, GAP_FOCUS_TEMPLATE

logger = logging.getLogger(__name__)


def summarize_content(content: str, content_type: str = "text", audience: str = "self", assessment_json: str = "") -> str:
    """Generate an audience-tailored summary."""
    logger.info(f"[TOOL] summarize_content: {audience}")

    client = genai.Client(api_key=settings.GOOGLE_API_KEY)

    # Get audience-specific template
    audience_template = AUDIENCE_TEMPLATES.get(audience, AUDIENCE_TEMPLATES["self"])

    # Build gap focus section if assessment provided
    assessment = json.loads(assessment_json) if assessment_json else {}
    if assessment:
        gap_focus = GAP_FOCUS_TEMPLATE.format(
            focus_areas=", ".join(assessment.get("focus_areas", [])),
            skip_areas=", ".join(assessment.get("skip_areas", [])),
        )
    else:
        gap_focus = ""

    # Format audience template with gap focus
    audience_template = audience_template.format(gap_focus=gap_focus)

    # Build the prompt using the detailed template
    prompt = SUMMARIZE_PROMPT.format(
        content=content[:8000] if content_type == "text" else "[PDF Content]",
        audience=audience,
        audience_template=audience_template,
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
            system_instruction=SUMMARIZER_SYSTEM_PROMPT,
            temperature=0.5,
            response_mime_type="application/json",
        ),
    )

    return response.text
