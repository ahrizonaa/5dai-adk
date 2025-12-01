"""FastAPI application for the SkillScape Agent Service.

This service implements a multi-agent system using Google ADK:
- AssessAgent: Generates knowledge assessment quizzes
- ContentTriagePipeline (SequentialAgent): Score → Organize
- SummarizeAgent: Creates audience-tailored summaries
"""

import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .agents import run_assess, run_triage, run_summarize
from .schemas import AssessRequest, AssessAnswersRequest, SummarizeRequest
from .schemas.responses import (
    QuizQuestion,
    QuizResponse,
    TopicAssessment,
    AssessmentResult,
    ContentNodeMetadata,
    AISuggestion,
    OrganizeResponse,
    SummaryContent,
    SummarizeResponse,
    TriageResponse,
    ContentMedium,
    ProgressStatus,
    Audience,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown."""
    logger.info(f"Starting SkillScape Agent Service on {settings.HOST}:{settings.PORT}")

    if not settings.is_configured:
        logger.warning("GOOGLE_API_KEY not configured")

    yield

    logger.info("Shutting down")


app = FastAPI(
    title="SkillScape Agent Service",
    description="Multi-agent AI system for intelligent learning content management using Google ADK.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def tracing_middleware(request: Request, call_next: Callable) -> Response:
    """Add request tracing."""
    trace_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    response = await call_next(request)

    duration_ms = (time.time() - start_time) * 1000
    logger.info(f"{request.method} {request.url.path} - {response.status_code} ({duration_ms:.0f}ms)")

    response.headers["X-Trace-ID"] = trace_id
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Health & Config
# =============================================================================

@app.get("/")
async def root():
    """Health check."""
    return {
        "service": "SkillScape Agent Service",
        "version": "1.0.0",
        "status": "healthy",
        "configured": settings.is_configured,
    }


@app.get("/config")
async def get_config():
    """Get service configuration."""
    return {
        "configured": settings.is_configured,
        "model": settings.AI_MODEL,
        "environment": settings.ENVIRONMENT,
    }


# =============================================================================
# REST API Endpoints (Multi-Agent System)
# =============================================================================

@app.post("/assess", response_model=QuizResponse)
async def assess_content(request: AssessRequest):
    """Generate quiz questions using the AssessAgent.

    This endpoint uses a single ADK agent with the generate_quiz tool
    to create a knowledge assessment quiz from the provided content.
    """
    if not settings.is_configured:
        raise HTTPException(status_code=503, detail="API key not configured")

    try:
        result = await run_assess(
            content=request.content,
            content_type=request.content_type,
            num_questions=request.num_questions,
        )

        return QuizResponse(
            session_id=result.get("session_id", ""),
            status="awaiting_answers",
            content_title=result.get("title", "Untitled"),
            topics=result.get("topics", []),
            questions=[
                QuizQuestion(
                    id=q["id"],
                    topic=q.get("topic", "General"),
                    question=q["question"],
                    options=q.get("options", {}),
                )
                for q in result.get("questions", [])
            ],
        )
    except Exception as e:
        logger.error(f"Assessment failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/assess/answers", response_model=TriageResponse)
async def submit_assessment_answers(request: AssessAnswersRequest):
    """Run the ContentTriagePipeline: Score → Organize.

    This endpoint invokes the SequentialAgent pattern:
    1. ScoreAgent evaluates quiz answers and produces assessment results
    2. OrganizeAgent uses the assessment to set progress and extract metadata

    The assessment results flow from ScoreAgent to OrganizeAgent via output_key.
    """
    if not settings.is_configured:
        raise HTTPException(status_code=503, detail="API key not configured")

    try:
        result = await run_triage(
            quiz_session_id=request.session_id,
            answers=request.answers,
            content=request.content,
            content_type=request.content_type,
            url=request.url or "",
        )

        logger.info(f"Triage result: {result}")

        assessment_data = result.get("assessment", {})
        org_data = result.get("organization", {})

        # Check if scoring failed (quiz session not found)
        if "error" in assessment_data:
            logger.error(f"Score quiz failed: {assessment_data}")
            raise HTTPException(
                status_code=400,
                detail=f"Quiz scoring failed: {assessment_data.get('error')}. The quiz session may have expired."
            )

        # Build assessment result
        assessment = AssessmentResult(
            session_id=assessment_data.get("session_id", request.session_id),
            status="complete",
            content_title=assessment_data.get("title", "Untitled"),
            topics_assessed=[
                TopicAssessment(
                    topic=t["topic"],
                    score=t["score"],
                    status=t["status"],
                    questions_correct=t["questions_correct"],
                    questions_total=t["questions_total"],
                )
                for t in assessment_data.get("topics_assessed", [])
            ],
            overall_knowledge=assessment_data.get("overall_knowledge", 0),
            focus_areas=assessment_data.get("focus_areas", []),
            skip_areas=assessment_data.get("skip_areas", []),
        )

        # Build organization result - extract from nested content_node if present
        node_data = org_data.get("content_node", org_data)
        suggestion_data = org_data.get("ai_suggestion", {})

        medium = node_data.get("medium", "article").lower()
        valid_mediums = {m.value for m in ContentMedium}
        medium_enum = ContentMedium(medium) if medium in valid_mediums else ContentMedium.ARTICLE

        status = node_data.get("status", "not_started").lower()
        valid_statuses = {s.value for s in ProgressStatus}
        status_enum = ProgressStatus(status) if status in valid_statuses else ProgressStatus.NOT_STARTED

        content_node = ContentNodeMetadata(
            title=node_data.get("title", "Untitled")[:60],
            medium=medium_enum,
            subjects=node_data.get("subjects", [])[:3],
            url=request.url,
            status=status_enum,
            progressPercent=min(100, max(0, node_data.get("progressPercent", 0))),
            author=node_data.get("author"),
            source=node_data.get("source"),
            tags=node_data.get("tags", [])[:5],
        )

        # Use ai_suggestion from organize result if available
        ai_suggestion = AISuggestion(
            title=suggestion_data.get("title", content_node.title),
            medium=content_node.medium,
            subjects=suggestion_data.get("subjects", content_node.subjects),
            tags=suggestion_data.get("tags", content_node.tags),
            isNewSubject=suggestion_data.get("isNewSubject", False),
            confidence=suggestion_data.get("confidence", 0.8),
        )

        organization = OrganizeResponse(
            content_node=content_node,
            ai_suggestion=ai_suggestion,
        )

        return TriageResponse(assessment=assessment, organization=organization)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Triage pipeline failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize_content(request: SummarizeRequest):
    """Generate audience-tailored summary using the SummarizeAgent.

    This endpoint uses a single ADK agent with the summarize_content tool
    to create a summary tailored to the specified audience.
    """
    if not settings.is_configured:
        raise HTTPException(status_code=503, detail="API key not configured")

    try:
        result = await run_summarize(
            content=request.content,
            content_type=request.content_type,
            audience=request.audience,
        )

        audience_lower = request.audience.lower()
        audience_enum = Audience(audience_lower) if audience_lower in ["engineering", "business", "self"] else Audience.SELF

        summary = SummaryContent(
            audience=audience_enum,
            content=result.get("summary", ""),
            key_takeaways=result.get("key_takeaways", []),
            code_examples=result.get("code_examples") if request.audience == "engineering" else None,
        )

        return SummarizeResponse(
            content_title=result.get("title", "Untitled"),
            summary=summary,
        )
    except Exception as e:
        logger.error(f"Summarization failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.is_development,
    )
