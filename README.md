# SkillScape Agent Service

> **Submission Track: Agents for Good (Education)**

A multi-agent AI system for managing educational resources—automatically assessing prior knowledge, organizing content metadata, and generating audience-specific summaries.

## The Problem

Educational content accumulates from many sources: online courses, PDFs, research papers, YouTube videos, podcasts. Managing this creates real problems:

- **No unified catalog** — Content is scattered across platforms with no central view
- **Manual metadata entry** — Adding title, subject, and tags for each resource is tedious
- **Inaccurate progress tracking** — Everything starts at 0% even if you already know the material
- **One-size-fits-all summaries** — Technical content needs different summaries for engineers vs. stakeholders

## The Solution

SkillScape Agent Service uses AI agents to automate content management:

1. **Knowledge Assessment** — Generate a quiz from content, score answers, determine what you already know
2. **Automatic Metadata Extraction** — Extract title, subject, medium type, and source from content
3. **Intelligent Progress Setting** — Set starting progress based on assessment (score 70%? start at 70%)
4. **Audience-Tailored Summaries** — Generate summaries for engineering, business, or personal use

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SkillScape Agent Service                             │
│                         (FastAPI + Google ADK)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────┐     ┌───────────────────┐     ┌──────────────────┐  │
│  │ Knowledge         │     │ Knowledge         │     │ Knowledge        │  │
│  │ Assessor          │────▶│ Organizer         │     │ Summarizer       │  │
│  │                   │     │                   │     │                  │  │
│  │ Tools:            │     │ Tools:            │     │ Tools:           │  │
│  │ • generate_quiz   │     │ • organize_content│     │ • summarize      │  │
│  │ • score_answers   │     │                   │     │                  │  │
│  └─────────┬─────────┘     └─────────┬─────────┘     └────────┬─────────┘  │
│            │                         │                        │            │
│            │    Session Store        │                        │            │
│            │    (Quiz State)         │                        │            │
│            ▼                         ▼                        ▼            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Google Gemini API                            │   │
│  │                       (gemini-2.5-flash)                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     Observability Layer                             │   │
│  │              (Structured Logging + Request Tracing)                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Sequential Agent Flow

```
                    ┌──────────────────┐
                    │  User Uploads    │
                    │  Learning Content│
                    └────────┬─────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │     Knowledge Assessor       │
              │                              │
              │  1. Analyze content          │
              │  2. Generate quiz            │
              │  3. Score answers            │
              │  4. Return: focus_areas,     │
              │     skip_areas, progress %   │
              └──────────────┬───────────────┘
                             │
                             │ assessment results
                             ▼
              ┌──────────────────────────────┐
              │     Knowledge Organizer      │
              │                              │
              │  1. Extract metadata         │
              │  2. Apply assessment progress│
              │  3. Categorize subjects      │
              │  4. Return: ContentNode      │
              └──────────────┬───────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │    Knowledge Summarizer      │
              │         (Optional)           │
              │                              │
              │  Generate audience-tailored  │
              │  summary focusing on gaps    │
              └──────────────────────────────┘
```

---

## Key Concepts Demonstrated

| ADK Concept | Implementation |
|-------------|----------------|
| **Multi-agent System** | 3 specialized LLM-powered agents working together |
| **Custom Tools** | `FunctionTool` implementations: `generate_quiz_tool`, `score_answers_tool`, `organize_content_tool`, `summarize_content_tool` |
| **Sessions & State** | `QuizSessionStore` maintains quiz state across 2-step assessment flow |
| **Sequential Agents** | Assessor output feeds into Organizer for accurate progress tracking |
| **Observability** | Structured logging with trace IDs, request duration metrics |
| **Deployment** | Dockerfile + Google Cloud Run configuration |

---

## Agents

| Agent | Purpose | Tools | Endpoint |
|-------|---------|-------|----------|
| **AssessAgent** | Generate adaptive quiz from content | `generate_quiz` | `POST /assess` |
| **ContentTriagePipeline** | Sequential: Score answers → Organize content | `score_quiz`, `organize_content` | `POST /assess/answers` |
| **SummarizeAgent** | Generate audience-tailored summaries | `summarize_content` | `POST /summarize` |

### ContentTriagePipeline (SequentialAgent)

The triage pipeline demonstrates the **SequentialAgent** pattern from ADK:

```python
# ScoreAgent output is stored in session state via output_key
score_agent = Agent(
    tools=[FunctionTool(score_quiz)],
    output_key="assessment",  # Stored for next agent
)

# OrganizeAgent receives assessment via placeholder injection
organize_agent = Agent(
    instruction="...Use the assessment results: {assessment}...",
    tools=[FunctionTool(organize_content)],
    output_key="organization",
)

# SequentialAgent orchestrates the flow
content_triage_pipeline = SequentialAgent(
    sub_agents=[score_agent, organize_agent],  # Runs in order
)
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Google API Key ([Get one from AI Studio](https://aistudio.google.com/))

### Setup

```bash
cd adk

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### Run Locally

```bash
# Development server with auto-reload
uvicorn app.main:app --reload --port 7020

# Or run directly
python -m app.main
```

### API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:7020/docs
- **ReDoc**: http://localhost:7020/redoc

---

## API Usage

### Complete Assessment Flow

**Step 1: Generate Quiz**
```bash
curl -X POST http://localhost:7020/assess \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your learning content text here...",
    "content_type": "text",
    "num_questions": 5
  }'
```

Response:
```json
{
  "session_id": "abc-123",
  "status": "awaiting_answers",
  "content_title": "Introduction to Machine Learning",
  "topics": ["Supervised Learning", "Neural Networks", "Model Evaluation"],
  "questions": [
    {
      "id": "q1",
      "topic": "Supervised Learning",
      "question": "What is the main difference between classification and regression?",
      "options": {
        "A": "Classification predicts categories, regression predicts continuous values",
        "B": "They are the same thing",
        "C": "Regression only works with images",
        "D": "Classification requires more data"
      }
    }
  ]
}
```

**Step 2: Submit Answers (Triage Pipeline)**

This endpoint runs the **SequentialAgent** pipeline: Score → Organize

```bash
curl -X POST http://localhost:7020/assess/answers \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc-123",
    "answers": {"q1": "A", "q2": "B", "q3": "A"},
    "content": "Your learning content...",
    "content_type": "text",
    "url": "https://example.com/ml-course"
  }'
```

Response includes BOTH assessment AND organization (from SequentialAgent):
```json
{
  "assessment": {
    "session_id": "abc-123",
    "status": "complete",
    "content_title": "Introduction to Machine Learning",
    "overall_knowledge": 0.67,
    "topics_assessed": [
      {"topic": "Supervised Learning", "score": 1.0, "status": "proficient"},
      {"topic": "Neural Networks", "score": 0.5, "status": "needs_review"}
    ],
    "focus_areas": ["Neural Networks"],
    "skip_areas": ["Supervised Learning"]
  },
  "organization": {
    "content_node": {
      "title": "Introduction to Machine Learning",
      "medium": "course",
      "subjects": ["AI", "Machine Learning"],
      "status": "in_progress",
      "progressPercent": 67,
      "source": "example.com"
    },
    "ai_suggestion": {
      "title": "Introduction to Machine Learning",
      "subjects": ["AI"],
      "confidence": 0.95
    }
  }
}
```

The `progressPercent: 67` is automatically set from the assessment score!

---

## Project Structure

```
adk/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app with REST endpoints
│   ├── config.py            # Configuration & logging setup
│   │
│   ├── agents/              # ADK Agent definitions
│   │   ├── __init__.py      # Exports: run_assess, run_triage, run_summarize
│   │   ├── assess_agent.py      # Single agent with generate_quiz tool
│   │   ├── triage_pipeline.py   # SequentialAgent: Score → Organize
│   │   └── summarize_agent.py   # Single agent for audience summaries
│   │
│   ├── tools/               # FunctionTool implementations
│   │   ├── __init__.py      # Exports all tools
│   │   ├── state.py         # Shared quiz_store (session state)
│   │   ├── generate_quiz.py # Generates assessment questions
│   │   ├── score_quiz.py    # Scores answers, tracks topics
│   │   ├── organize_content.py  # Extracts metadata, applies progress
│   │   └── summarize_content.py # Creates audience-tailored summaries
│   │
│   ├── prompts/             # Detailed prompt templates
│   │   ├── assessor.py      # Assessment generation prompts
│   │   ├── organizer.py     # Content organization prompts
│   │   └── summarizer.py    # Summary generation prompts
│   │
│   └── schemas/             # Pydantic models
│       ├── requests.py      # API request models
│       └── responses.py     # API response models
│
├── requirements.txt
├── Dockerfile               # Container deployment
├── .env.example             # Environment template
└── README.md
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google AI API key (required) | - |
| `AI_MODEL` | Gemini model to use | `gemini-2.5-flash` |
| `PORT` | Server port | `7020` |
| `HOST` | Server host | `0.0.0.0` |
| `ENVIRONMENT` | development/production | `development` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `ENABLE_TRACING` | Enable request tracing | `true` |

---

## Deployment

### Docker

```bash
docker build -t skillscape-agents .
docker run -p 7020:7020 -e GOOGLE_API_KEY=your_key_here skillscape-agents
```

### Google Cloud Run

```bash
gcloud run deploy skillscape-agents \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=your_key_here
```
