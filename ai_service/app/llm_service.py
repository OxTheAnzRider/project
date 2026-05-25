"""OpenAI-backed question generation and semantic grading with local fallback."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, ValidationError, field_validator

log = logging.getLogger("ai.llm_service")


def _load_openai_env() -> None:
    """Load local env files so the AI service sees OpenAI config when run alone."""
    try:
        from dotenv import load_dotenv
    except Exception as exc:
        log.debug("python-dotenv unavailable; relying on process env only: %s", exc)
        return

    ai_service_dir = Path(__file__).resolve().parents[1]
    project_root = ai_service_dir.parent
    for env_path in (
        ai_service_dir / ".env",
        project_root / ".env",
        project_root / "backend" / ".env",
    ):
        if env_path.exists():
            load_dotenv(env_path, override=False)


_load_openai_env()

QuestionType = Literal["definition", "conceptual", "application", "analysis"]
EXPECTED_DISTRIBUTION = {
    "definition": 8,
    "conceptual": 8,
    "application": 7,
    "analysis": 7,
}


class LLMQuestion(BaseModel):
    id: str = Field(min_length=1)
    question: str = Field(min_length=8)
    expected_answer: str = Field(min_length=8)
    question_type: QuestionType
    difficulty: str = Field(min_length=1)
    key_concepts: list[str] = Field(default_factory=list)
    rubric: str = Field(min_length=8)
    points: int = Field(ge=1, le=10)


class LLMQuestionSet(BaseModel):
    questions: list[LLMQuestion]

    @field_validator("questions")
    @classmethod
    def validate_questions(cls, questions: list[LLMQuestion]):
        if len(questions) != 30:
            raise ValueError("Question set must contain exactly 30 questions")
        counts = {key: 0 for key in EXPECTED_DISTRIBUTION}
        ids = set()
        for question in questions:
            counts[question.question_type] += 1
            if question.id in ids:
                raise ValueError(f"Duplicate question id: {question.id}")
            ids.add(question.id)
        if counts != EXPECTED_DISTRIBUTION:
            raise ValueError(f"Invalid question distribution: {counts}")
        return questions


class LLMGrade(BaseModel):
    question_id: str = Field(min_length=1)
    score: float = Field(ge=0, le=100)
    passed: bool
    feedback: str = ""
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0, le=1)
    grading_reason: str = ""


class LLMGradeSet(BaseModel):
    grades: list[LLMGrade]


def _client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        log.info("OPENAI_API_KEY is not set; LLM disabled")
        return None
    try:
        from openai import OpenAI
    except Exception as exc:
        log.warning("OpenAI SDK unavailable; LLM disabled: %s", exc)
        return None
    try:
        timeout = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "180"))
    except ValueError:
        timeout = 180
    return OpenAI(api_key=api_key, timeout=timeout)


def llm_configuration_status() -> dict:
    """Return non-secret LLM configuration state for diagnostics/health checks."""
    return {
        "openai_key_configured": bool(os.getenv("OPENAI_API_KEY")),
        "openai_model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    }


def _json_chat(system: str, user: str) -> dict | None:
    client = _client()
    if client is None:
        return None
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    try:
        response = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)
    except Exception as exc:
        log.warning("OpenAI request failed; falling back locally: %s", exc)
        return None


def generate_questions_with_llm(
    material_text: str,
    key_concepts: list[str],
    difficulty: str,
) -> list[dict] | None:
    """Return normalized internal question dicts or None for fallback."""
    question_plan = (
        [{"id": f"q_{idx}", "question_type": "definition"} for idx in range(1, 9)]
        + [{"id": f"q_{idx}", "question_type": "conceptual"} for idx in range(9, 17)]
        + [{"id": f"q_{idx}", "question_type": "application"} for idx in range(17, 24)]
        + [{"id": f"q_{idx}", "question_type": "analysis"} for idx in range(24, 31)]
    )
    system = (
        "You generate valid JSON only. Build assessment questions from course "
        "material. Do not invent unrelated facts. Follow the provided question_plan "
        "exactly: every output item must use the same id and question_type from "
        "that plan."
    )
    payload = {
        "task": "Generate exactly 30 assessment questions.",
        "distribution": EXPECTED_DISTRIBUTION,
        "question_plan": question_plan,
        "difficulty": difficulty,
        "key_concepts": key_concepts,
        "required_json_shape": {
            "questions": [{
                "id": "q_1",
                "question": "string",
                "expected_answer": "string",
                "question_type": "definition|conceptual|application|analysis",
                "difficulty": difficulty,
                "key_concepts": ["string"],
                "rubric": "string",
                "points": 1,
            }]
        },
        "material": material_text[:24000],
    }

    parsed = None
    last_error = None
    for attempt in range(2):
        if attempt == 1:
            payload["retry_instruction"] = (
                "Your previous JSON failed validation. Regenerate the complete "
                "response using exactly the ids and question_type values from "
                "question_plan. Do not change the distribution."
            )
            payload["previous_validation_error"] = str(last_error)
        raw = _json_chat(system, json.dumps(payload))
        if raw is None:
            return None
        try:
            parsed = LLMQuestionSet.model_validate(raw)
            break
        except ValidationError as exc:
            last_error = exc
            log.warning("LLM question output failed validation: %s", exc)
    if parsed is None:
        return None

    log.info("LLM question generation succeeded")
    return [
        {
            "question_id": item.id,
            "question": item.question,
            "type": item.question_type,
            "difficulty": item.difficulty,
            "concept": ", ".join(item.key_concepts) if item.key_concepts else item.question_type,
            "key_concepts": item.key_concepts,
            "points": item.points,
            "expected_answer": item.expected_answer,
            "rubric": item.rubric,
            "generation_method": "llm",
        }
        for item in parsed.questions
    ]


def grade_answers_with_llm(
    questions_with_expected_answers: list[dict],
    student_answers: list[dict],
) -> dict[str, dict] | None:
    """Batch-grade answers and return a question_id keyed mapping."""
    answer_map = {item["question_id"]: item.get("answer_text", "") for item in student_answers}
    payload = []
    for question in questions_with_expected_answers:
        payload.append({
            "question_id": question.get("question_id"),
            "question": question.get("question"),
            "question_type": question.get("type"),
            "expected_answer": question.get("expected_answer"),
            "rubric": question.get("rubric"),
            "student_answer": answer_map.get(question.get("question_id"), ""),
        })

    system = (
        "You grade learner answers using the supplied expected answers and rubrics. "
        "Return valid JSON only. Be fair to equivalent wording, but do not reward "
        "answers that miss the required concept. Keep the feedback tone aligned "
        "with the numeric score: use excellent/strong language only for high scores, "
        "and clearly name missing rubric points for low or partial scores."
    )
    user = json.dumps({
        "task": "Grade all answers.",
        "required_json_shape": {
            "grades": [{
                "question_id": "q_1",
                "score": 0,
                "passed": False,
                "feedback": "string",
                "strengths": ["string"],
                "weaknesses": ["string"],
                "confidence_score": 0.0,
                "grading_reason": "string",
            }]
        },
        "items": payload,
    })
    raw = _json_chat(system, user)
    if raw is None:
        return None
    try:
        parsed = LLMGradeSet.model_validate(raw)
    except ValidationError as exc:
        log.warning("LLM grading output failed validation: %s", exc)
        return None

    grade_map = {grade.question_id: grade.model_dump() for grade in parsed.grades}
    if len(grade_map) != len(questions_with_expected_answers):
        log.warning("LLM returned %s grades for %s questions", len(grade_map), len(questions_with_expected_answers))
        return None
    log.info("LLM batch grading succeeded")
    return grade_map
