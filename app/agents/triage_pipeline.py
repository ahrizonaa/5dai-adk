"""ContentTriagePipeline - Sequential agent for Score → Organize."""

import json

from google.adk.agents import Agent, SequentialAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import FunctionTool
from google.genai import types

from ..config import settings
from ..tools import score_quiz, organize_content

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

score_agent = Agent(
    model=Gemini(model=settings.AI_MODEL, retry_options=retry_config),
    name="ScoreAgent",
    description="Scores quiz answers and produces assessment results",
    instruction="""You are a scoring specialist. Use the score_quiz tool to evaluate
    the user's answers and determine their knowledge level across topics.""",
    tools=[FunctionTool(score_quiz)],
    output_key="assessment",
)

organize_agent = Agent(
    model=Gemini(model=settings.AI_MODEL, retry_options=retry_config),
    name="OrganizeAgent",
    description="Extracts metadata and organizes content for the knowledge graph",
    instruction="""You are a content organizer. Use the organize_content tool to extract
    metadata from the content. Use the assessment results to set the progress level:
    Assessment: {assessment}""",
    tools=[FunctionTool(organize_content)],
    output_key="organization",
)

content_triage_pipeline = SequentialAgent(
    name="ContentTriagePipeline",
    description="Scores quiz answers then organizes content based on assessment",
    sub_agents=[score_agent, organize_agent],
)


async def run_triage(quiz_session_id: str, answers: dict, content: str, content_type: str, url: str = "") -> dict:
    """Run the sequential pipeline: Score → Organize."""
    runner = InMemoryRunner(agent=content_triage_pipeline, app_name="triage_app")

    session = await runner.session_service.create_session(
        app_name="triage_app",
        user_id="api_user",
    )

    answers_json = json.dumps(answers)
    message = f"""Process this content triage:

1. Score the quiz (session_id: {quiz_session_id}, answers: {answers_json})
2. Then organize the content for the graph (content_type: {content_type}, url: {url})

Content:
{content[:2000]}"""

    final_response = None
    async for event in runner.run_async(
        user_id="api_user",
        session_id=session.id,
        new_message=types.Content(role="user", parts=[types.Part.from_text(text=message)]),
    ):
        if hasattr(event, 'content') and event.content:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    final_response = part.text

    if final_response:
        try:
            return json.loads(final_response)
        except json.JSONDecodeError:
            pass

    # Fallback: run tools directly
    score_result = json.loads(score_quiz(quiz_session_id, answers_json))
    org_result = json.loads(organize_content(content, content_type, url, json.dumps(score_result)))
    return {"assessment": score_result, "organization": org_result}
