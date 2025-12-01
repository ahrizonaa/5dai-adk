"""SummarizeAgent - Creates audience-tailored summaries."""

import json

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import FunctionTool
from google.genai import types

from ..config import settings
from ..tools import summarize_content

# Retry configuration
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

summarize_agent = Agent(
    model=Gemini(model=settings.AI_MODEL, retry_options=retry_config),
    name="SummarizeAgent",
    description="Creates audience-tailored summaries of learning content",
    instruction="""You are a summarization specialist. Use the summarize_content tool
    to create a summary tailored to the specified audience.""",
    tools=[FunctionTool(summarize_content)],
    output_key="summary",
)


async def run_summarize(content: str, content_type: str, audience: str) -> dict:
    """Run the summarize agent."""
    runner = InMemoryRunner(agent=summarize_agent, app_name="summarize_app")

    # Create session first - InMemoryRunner requires this
    session = await runner.session_service.create_session(
        app_name="summarize_app",
        user_id="api_user",
    )

    message = f"Summarize this {content_type} content for a {audience} audience:\n{content[:3000]}"

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
    result = summarize_content(content, content_type, audience)
    return json.loads(result)
