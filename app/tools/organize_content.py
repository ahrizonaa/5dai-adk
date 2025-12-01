"""Organize content tool."""

import json
import base64
import logging

from google import genai
from google.genai import types

from ..config import settings
from ..prompts.organizer import ORGANIZER_SYSTEM_PROMPT, ORGANIZE_PROMPT, ASSESSMENT_SECTION_TEMPLATE

logger = logging.getLogger(__name__)


def organize_content(content: str, content_type: str = "text", url: str = "", assessment_json: str = "", existing_subjects: str = "") -> str:
    """Extract metadata and organize content for the learning graph."""
    logger.info(f"[TOOL] organize_content: type={content_type}, url={url}, content_len={len(content)}, has_assessment={bool(assessment_json)}")

    client = genai.Client(api_key=settings.GOOGLE_API_KEY)

    # Parse assessment if provided
    assessment = json.loads(assessment_json) if assessment_json else {}
    progress = int(assessment.get("overall_knowledge", 0) * 100)

    # Build assessment section if we have assessment data
    if assessment:
        assessment_section = ASSESSMENT_SECTION_TEMPLATE.format(
            overall_knowledge=progress,
            focus_areas=", ".join(assessment.get("focus_areas", [])),
            skip_areas=", ".join(assessment.get("skip_areas", [])),
            progress_percent=progress,
            status="completed" if progress >= 100 else "in_progress" if progress > 0 else "not_started",
        )
    else:
        assessment_section = "No assessment data provided."

    # Build the prompt using the detailed template
    prompt = ORGANIZE_PROMPT.format(
        content=content[:5000] if content_type == "text" else "[PDF Content]",
        url=url or "Not provided",
        existing_subjects=existing_subjects or "None yet",
        assessment_section=assessment_section,
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
            system_instruction=ORGANIZER_SYSTEM_PROMPT,
            temperature=0.3,
            response_mime_type="application/json",
        ),
    )

    result = json.loads(response.text)

    # Extract content_node if nested, otherwise use result directly
    if "content_node" in result:
        content_node = result["content_node"]
    else:
        content_node = result

    # Ensure progress and status are set from assessment
    content_node["progressPercent"] = progress
    content_node["status"] = "completed" if progress >= 100 else "in_progress" if progress > 0 else "not_started"

    logger.info(f"[TOOL] organize_content result: title={content_node.get('title')}, subjects={content_node.get('subjects')}, source={content_node.get('source')}")
    return json.dumps(result)
