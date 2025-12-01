"""AssessAgent - Generates knowledge assessment quizzes."""

import json

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import FunctionTool
from google.genai import types

from ..config import settings
from ..tools import generate_quiz

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

assess_agent = Agent(
    model=Gemini(model=settings.AI_MODEL, retry_options=retry_config),
    name="AssessAgent",
    description="Generates knowledge assessment quizzes from learning content",
    instruction="""You are an assessment specialist. When given learning content,
    use the generate_quiz tool to create a quiz that tests understanding of key concepts.""",
    tools=[FunctionTool(generate_quiz)],
    output_key="quiz_result",
)


async def run_assess(content: str, content_type: str, num_questions: int) -> dict:
    """Run the assess agent to generate a quiz."""
    runner = InMemoryRunner(agent=assess_agent, app_name="assess_app")

    session = await runner.session_service.create_session(
        app_name="assess_app",
        user_id="api_user",
    )

    message = f"Generate a {num_questions}-question quiz for this {content_type} content:\n{content[:2000]}"

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

    # Fallback: call tool directly
    result = generate_quiz(content, content_type, num_questions)
    return json.loads(result)
