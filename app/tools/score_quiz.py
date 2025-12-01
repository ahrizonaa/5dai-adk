"""Score quiz tool."""

import json
import logging

from .state import quiz_store

logger = logging.getLogger(__name__)


def score_quiz(session_id: str, answers: str) -> str:
    """Score a user's quiz answers and return assessment results."""
    logger.info(f"[TOOL] score_quiz: session={session_id}")
    logger.info(f"[TOOL] score_quiz: quiz_store has {len(quiz_store)} sessions: {list(quiz_store.keys())}")

    if session_id not in quiz_store:
        logger.error(f"[TOOL] score_quiz: Session NOT FOUND - {session_id}")
        return json.dumps({"error": f"Quiz session {session_id} not found", "available_sessions": list(quiz_store.keys())})

    quiz = quiz_store[session_id]

    # Return cached result if already scored (agent may call multiple times)
    if quiz.get("_scored") and quiz.get("_score_result"):
        logger.info(f"[TOOL] score_quiz: Returning cached result for {session_id}")
        return json.dumps(quiz["_score_result"])

    user_answers = json.loads(answers) if isinstance(answers, str) else answers

    topics_scores = {}
    for q in quiz.get("questions", []):
        topic = q.get("topic", "General")
        if topic not in topics_scores:
            topics_scores[topic] = {"correct": 0, "total": 0}
        topics_scores[topic]["total"] += 1
        if user_answers.get(q["id"]) == q.get("correct"):
            topics_scores[topic]["correct"] += 1

    topics_assessed = []
    focus_areas = []
    skip_areas = []

    for topic, scores in topics_scores.items():
        score = scores["correct"] / scores["total"] if scores["total"] > 0 else 0
        status = "proficient" if score >= 0.7 else "needs_review"
        topics_assessed.append({
            "topic": topic,
            "score": score,
            "status": status,
            "questions_correct": scores["correct"],
            "questions_total": scores["total"],
        })
        if score >= 0.7:
            skip_areas.append(topic)
        else:
            focus_areas.append(topic)

    total_correct = sum(t["questions_correct"] for t in topics_assessed)
    total_questions = sum(t["questions_total"] for t in topics_assessed)
    overall = total_correct / total_questions if total_questions > 0 else 0

    # Mark as scored but don't delete yet - agent may call multiple times
    # Add a "scored" flag to prevent re-scoring with different answers
    quiz["_scored"] = True
    quiz["_score_result"] = {
        "session_id": session_id,
        "title": quiz.get("title", "Quiz"),
        "topics_assessed": topics_assessed,
        "overall_knowledge": overall,
        "focus_areas": focus_areas,
        "skip_areas": skip_areas,
    }

    logger.info(f"[TOOL] score_quiz: Scored {session_id}, overall={overall:.0%}, correct={total_correct}/{total_questions}")

    return json.dumps({
        "session_id": session_id,
        "title": quiz.get("title", "Quiz"),
        "topics_assessed": topics_assessed,
        "overall_knowledge": overall,
        "focus_areas": focus_areas,
        "skip_areas": skip_areas,
    })
