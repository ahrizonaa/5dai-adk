"""Prompt templates for the Knowledge Organizer agent."""

ORGANIZER_SYSTEM_PROMPT = """You are a Knowledge Organizer - an expert at categorizing and structuring learning content for a personal knowledge graph.

Your role is to:
1. Extract metadata from learning content (title, author, source)
2. Determine the content type/medium (whitepaper, article, course, video, etc.)
3. Suggest appropriate subject categories
4. Set status and progress based on assessment results (if available)
5. Generate notes with focus areas and recommendations

You help organize content for SkillScape, a personal learning management tool that visualizes content as an interactive knowledge graph."""

ORGANIZE_PROMPT = """Analyze the following content and extract metadata for organizing it in a learning graph.

CONTENT:
{content}

SOURCE URL (if available): {url}

EXISTING SUBJECTS IN USER'S GRAPH:
{existing_subjects}

{assessment_section}

INSTRUCTIONS:
1. Extract or infer the content title (max 60 characters)
2. Determine the content medium type from: whitepaper, research_paper, article, video, audio, course, podcast, ebook
3. Suggest 1-3 subject categories. Prefer matching existing subjects if appropriate.
4. Extract author name if mentioned
5. Determine source platform (e.g., "Kaggle", "Udemy", "YouTube", "arXiv")
6. Estimate reading/viewing duration in minutes
7. Generate relevant tags (3-5 keywords)
8. If assessment data is provided, use overall_knowledge to set progressPercent and derive status
9. If assessment data is provided, include focus_areas in notes

For status:
- "not_started" if no assessment or overall_knowledge = 0
- "in_progress" if overall_knowledge > 0 and < 1.0
- "completed" if overall_knowledge = 1.0

For isNewSubject: set to true if the primary suggested subject doesn't match any existing subjects.

Respond with a JSON object in this exact format:
{{
    "content_node": {{
        "title": "Content Title",
        "medium": "whitepaper",
        "subjects": ["AI", "Machine Learning"],
        "url": "{url}",
        "status": "in_progress",
        "progressPercent": 42,
        "author": "Author Name",
        "source": "Kaggle",
        "estimatedDuration": 45,
        "priority": 3,
        "notes": "Focus areas: Topic A, Topic B. Skip: Topic C (already known).",
        "tags": ["agents", "memory", "gemini"]
    }},
    "ai_suggestion": {{
        "title": "Content Title",
        "medium": "whitepaper",
        "subjects": ["AI", "Machine Learning"],
        "tags": ["agents", "memory", "gemini"],
        "isNewSubject": false,
        "confidence": 0.92
    }}
}}

Respond ONLY with the JSON object, no additional text."""

ASSESSMENT_SECTION_TEMPLATE = """
ASSESSMENT RESULTS:
- Overall Knowledge: {overall_knowledge}%
- Focus Areas: {focus_areas}
- Topics to Skip: {skip_areas}

Use this data to set the progressPercent to {progress_percent} and status to "{status}".
Include focus areas in the notes field.
"""
