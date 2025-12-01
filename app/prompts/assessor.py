"""Prompt templates for the Knowledge Assessor agent."""

ASSESSOR_SYSTEM_PROMPT = """You are a Knowledge Assessor - an expert at evaluating what someone already knows about technical content.

Your role is to:
1. Analyze learning content to identify 3-5 key topics
2. Generate quiz questions that test understanding of these topics
3. Score responses to determine knowledge level
4. Provide actionable recommendations on what to focus on vs. skip

You help lifelong learners save time by quickly determining their existing knowledge level before investing time in new content."""

QUIZ_GENERATION_PROMPT = """Analyze the following content and generate a knowledge assessment quiz.

CONTENT:
{content}

INSTRUCTIONS:
1. Identify 3-5 key topics covered in this content
2. For each topic, generate {num_questions_per_topic} multiple-choice questions
3. Questions should test understanding, not just recall
4. Each question should have exactly 4 options (A, B, C, D)
5. Mark the correct answer for each question
6. Questions should range from fundamental to advanced

Respond with a JSON object in this exact format:
{{
    "title": "extracted or inferred title of the content",
    "topics": ["topic1", "topic2", "topic3"],
    "questions": [
        {{
            "id": "q1",
            "topic": "topic1",
            "question": "What is the main purpose of X?",
            "options": {{
                "A": "Option A text",
                "B": "Option B text",
                "C": "Option C text",
                "D": "Option D text"
            }},
            "correct_answer": "B"
        }}
    ]
}}

Generate exactly {total_questions} questions total, distributed across the identified topics.
Respond ONLY with the JSON object, no additional text."""

SCORING_PROMPT = """Score the following quiz answers and provide an assessment.

QUIZ DATA:
{quiz_data}

USER ANSWERS:
{user_answers}

INSTRUCTIONS:
1. Compare user answers against correct answers
2. Calculate score per topic (0.0 to 1.0)
3. Determine overall knowledge percentage
4. Identify focus areas (topics with low scores < 0.5)
5. Identify skip areas (topics with high scores >= 0.8)
6. Estimate remaining learning time based on content length and knowledge gaps

For status, use:
- "proficient" if score >= 0.8
- "needs_review" if score >= 0.5 and < 0.8
- "new" if score < 0.5

Respond with a JSON object in this exact format:
{{
    "topics_assessed": [
        {{
            "topic": "topic name",
            "score": 0.75,
            "status": "needs_review",
            "questions_correct": 2,
            "questions_total": 3
        }}
    ],
    "overall_knowledge": 0.65,
    "focus_areas": ["topics to study"],
    "skip_areas": ["topics already known"],
    "estimated_learning_time": "30 min"
}}

Respond ONLY with the JSON object, no additional text."""
