"""Prompt templates for the Knowledge Summarizer agent."""

SUMMARIZER_SYSTEM_PROMPT = """You are a Knowledge Summarizer - an expert at condensing learning content into actionable summaries tailored for different audiences.

Your role is to:
1. Analyze content structure and key concepts
2. Adapt summary style based on target audience
3. Focus on knowledge gaps if assessment data is provided
4. Produce clear, well-structured markdown summaries

You help lifelong learners share and retain knowledge effectively."""

AUDIENCE_TEMPLATES = {
    "engineering": """Create a technical summary for an engineering team.

FOCUS ON:
- Implementation details and architecture
- Code patterns and examples
- Technical trade-offs and considerations
- Integration points and APIs
- Performance implications
- Security considerations

STYLE:
- High technical depth
- Include code snippets where relevant
- Use precise technical terminology
- Focus on "how" and "why" of implementation

{gap_focus}""",

    "business": """Create an executive summary for business stakeholders.

FOCUS ON:
- Business value and ROI
- Use cases and applications
- Competitive landscape context
- User/customer impact
- Risk factors and mitigations
- Timeline and resource implications

STYLE:
- Clear, jargon-free language
- Lead with impact and value
- Use bullet points for scanability
- Include metrics where possible
- Keep technical details minimal

{gap_focus}""",

    "self": """Create a personal learning reference.

FOCUS ON:
- Key mental models and frameworks
- Gotchas and common mistakes
- Quick reference cheat sheet
- Things to remember long-term
- Connections to other knowledge
- Practical applications

STYLE:
- Concise and scannable
- Use mnemonics if helpful
- Highlight "aha" moments
- Include personal action items
- Format for quick lookup

{gap_focus}""",
}

SUMMARIZE_PROMPT = """Summarize the following content for the specified audience.

CONTENT:
{content}

TARGET AUDIENCE: {audience}

{audience_template}

INSTRUCTIONS:
1. Extract the main title/topic of the content
2. Create a well-structured markdown summary
3. Include 3-5 key takeaways as bullet points
4. For engineering audience, include relevant code examples if present
5. Keep the summary concise but comprehensive

Respond with a JSON object in this exact format:
{{
    "content_title": "Title of the content",
    "summary": {{
        "audience": "{audience}",
        "content": "## Summary\\n\\nYour markdown summary here...\\n\\n## Key Concepts\\n\\n...",
        "key_takeaways": [
            "First key point",
            "Second key point",
            "Third key point"
        ],
        "code_examples": ["// example code if engineering audience", null]
    }}
}}

For code_examples: include array of code snippets for engineering audience, null for others.

Respond ONLY with the JSON object, no additional text."""

GAP_FOCUS_TEMPLATE = """
KNOWLEDGE GAPS TO EMPHASIZE:
The user has identified these areas as needing focus: {focus_areas}
The user already knows these areas well (mention briefly): {skip_areas}

Emphasize the focus areas in your summary and keep skip areas brief.
"""
