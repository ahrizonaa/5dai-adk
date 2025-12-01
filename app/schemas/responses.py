"""Response schemas for API endpoints."""

from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class ContentMedium(str, Enum):
    """Valid content medium types."""

    WHITEPAPER = "whitepaper"
    RESEARCH_PAPER = "research_paper"
    ARTICLE = "article"
    VIDEO = "video"
    AUDIO = "audio"
    COURSE = "course"
    PODCAST = "podcast"
    EBOOK = "ebook"


class ProgressStatus(str, Enum):
    """Valid progress status values."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    ARCHIVED = "archived"


class Audience(str, Enum):
    """Valid audience types."""

    ENGINEERING = "engineering"
    BUSINESS = "business"
    SELF = "self"


class QuizQuestion(BaseModel):
    """A single quiz question."""

    id: str = Field(..., description="Unique question identifier")
    topic: str = Field(..., description="Topic this question assesses")
    question: str = Field(..., description="The question text")
    options: dict[str, str] = Field(
        ..., description="Answer options: {'A': '...', 'B': '...', 'C': '...', 'D': '...'}"
    )


class QuizResponse(BaseModel):
    """Response containing quiz questions."""

    session_id: str = Field(..., description="Session ID for submitting answers")
    status: str = Field(default="awaiting_answers", description="Current status")
    content_title: str = Field(..., description="Extracted title of the content")
    topics: list[str] = Field(..., description="Topics identified in the content")
    questions: list[QuizQuestion] = Field(..., description="Quiz questions to answer")


class TopicAssessment(BaseModel):
    """Assessment result for a single topic."""

    topic: str = Field(..., description="Topic name")
    score: float = Field(..., ge=0.0, le=1.0, description="Score from 0.0 to 1.0")
    status: str = Field(
        ..., description="Status: 'proficient', 'needs_review', or 'new'"
    )
    questions_correct: int = Field(..., description="Number of correct answers")
    questions_total: int = Field(..., description="Total questions for this topic")


class AssessmentResult(BaseModel):
    """Complete assessment results after answering quiz."""

    session_id: str = Field(..., description="Session ID")
    status: str = Field(default="complete", description="Assessment status")
    content_title: str = Field(..., description="Title of assessed content")
    topics_assessed: list[TopicAssessment] = Field(
        ..., description="Assessment per topic"
    )
    overall_knowledge: float = Field(
        ..., ge=0.0, le=1.0, description="Overall knowledge percentage"
    )
    focus_areas: list[str] = Field(
        ..., description="Topics to focus on (low scores)"
    )
    skip_areas: list[str] = Field(
        ..., description="Topics user already knows (high scores)"
    )
    estimated_learning_time: Optional[str] = Field(
        default=None, description="Estimated time to learn remaining content"
    )


class ContentNodeMetadata(BaseModel):
    """Metadata for a SkillScape ContentNode."""

    title: str = Field(..., description="Content title")
    medium: ContentMedium = Field(..., description="Content medium type")
    subjects: list[str] = Field(..., description="Subject categories")
    url: Optional[str] = Field(default=None, description="Source URL")
    status: ProgressStatus = Field(
        default=ProgressStatus.NOT_STARTED, description="Progress status"
    )
    progressPercent: int = Field(
        default=0, ge=0, le=100, description="Progress percentage"
    )
    author: Optional[str] = Field(default=None, description="Content author")
    source: Optional[str] = Field(
        default=None, description="Platform/source (e.g., 'Kaggle', 'Udemy')"
    )
    estimatedDuration: Optional[int] = Field(
        default=None, description="Duration in minutes"
    )
    priority: int = Field(default=3, ge=1, le=5, description="Priority 1-5")
    notes: Optional[str] = Field(default=None, description="Notes with focus areas")
    tags: list[str] = Field(default_factory=list, description="Content tags")


class AISuggestion(BaseModel):
    """AI suggestion for content organization."""

    title: str = Field(..., description="Suggested title")
    medium: ContentMedium = Field(..., description="Suggested medium type")
    subjects: list[str] = Field(..., description="Suggested subjects")
    tags: list[str] = Field(default_factory=list, description="Suggested tags")
    isNewSubject: bool = Field(
        default=False, description="Whether this suggests a new subject"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score 0.0-1.0"
    )


class OrganizeResponse(BaseModel):
    """Response from organize endpoint."""

    content_node: ContentNodeMetadata = Field(
        ..., description="ContentNode metadata for SkillScape"
    )
    ai_suggestion: AISuggestion = Field(..., description="AI suggestion details")


class SummaryContent(BaseModel):
    """Generated summary content."""

    audience: Audience = Field(..., description="Target audience")
    content: str = Field(..., description="Markdown-formatted summary")
    key_takeaways: list[str] = Field(..., description="Key points from the content")
    code_examples: Optional[list[str]] = Field(
        default=None, description="Code examples (for engineering audience)"
    )


class SummarizeResponse(BaseModel):
    """Response from summarize endpoint."""

    content_title: str = Field(..., description="Title of summarized content")
    summary: SummaryContent = Field(..., description="Generated summary")


class TriageResponse(BaseModel):
    """Response from triage pipeline (Score → Organize)."""

    assessment: AssessmentResult = Field(..., description="Quiz assessment results")
    organization: OrganizeResponse = Field(..., description="Content organization for graph")
