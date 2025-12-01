"""Request schemas for API endpoints."""

from typing import Optional
from pydantic import BaseModel, Field


class AssessRequest(BaseModel):
    """Request to start a knowledge assessment."""

    content: str = Field(..., description="Base64 encoded PDF or plain text content")
    content_type: str = Field(
        default="text", description="Content type: 'pdf' or 'text'"
    )
    num_questions: int = Field(
        default=5, ge=3, le=10, description="Number of quiz questions to generate"
    )


class AssessAnswersRequest(BaseModel):
    """Request to submit quiz answers and run the triage pipeline (Score → Organize)."""

    session_id: str = Field(..., description="Session ID from initial assess request")
    answers: dict[str, str] = Field(
        ..., description="Map of question_id to selected answer (A, B, C, or D)"
    )
    # Content fields for the organize step in the triage pipeline
    content: str = Field(..., description="Base64 encoded PDF or plain text content")
    content_type: str = Field(default="text", description="Content type: 'pdf' or 'text'")
    url: Optional[str] = Field(default=None, description="Source URL if available")


class OrganizeRequest(BaseModel):
    """Request to organize content for the learning graph."""

    content: str = Field(..., description="Base64 encoded PDF or plain text content")
    content_type: str = Field(
        default="text", description="Content type: 'pdf' or 'text'"
    )
    url: Optional[str] = Field(default=None, description="Source URL if available")
    assessment: Optional[dict] = Field(
        default=None, description="Assessment results from /assess endpoint"
    )
    existing_subjects: list[str] = Field(
        default_factory=list, description="List of existing subject names in user's graph"
    )


class SummarizeRequest(BaseModel):
    """Request to summarize content for a specific audience."""

    content: str = Field(..., description="Base64 encoded PDF or plain text content")
    content_type: str = Field(
        default="text", description="Content type: 'pdf' or 'text'"
    )
    audience: str = Field(
        ..., description="Target audience: 'engineering', 'business', or 'self'"
    )
    assessment: Optional[dict] = Field(
        default=None, description="Assessment results to focus summary on knowledge gaps"
    )
