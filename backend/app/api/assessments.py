"""
backend/app/api/assessments.py — Q-by-Q assessment and issuance workflow.

Flow:
1. issueruploads material:       POST /api/assessments/materials/ingest
2. Learner starts assessment:         POST /api/assessments/create
3. Learner submits each answer:       POST /api/assessments/{id}/answers/submit
4. Learner submits for grading:       POST /api/assessments/{id}/grade
5. Learner views final result/cert:   GET  /api/assessments/{id}/result
"""

from datetime import datetime, timezone
import json
import logging
import random
from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.db import (
    Assessment,
    AssessmentTemplate,
    AuditLog,
    Certificate,
    CourseEnrollment,
    EventTypeEnum,
    Issuer,
    Learner,
    Material,
    OutcomeEnum,
    SessionLocal,
)
from app.services.blockchain import get_blockchain_service
from app.services.certificate_pdf import build_certificate_pdf_bytes, generate_verification_code
from app.services.ipfs import pin_file, pin_json

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/assessments", tags=["assessments"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


settings = get_settings()


class MaterialIngestionRequest(BaseModel):
    issuer_id: str
    programme: str
    title: str
    content: str
    difficulty_level: str = "intermediate"
    topics: Optional[List[str]] = None


class AssessmentCreationRequest(BaseModel):
    learner_id: str
    material_id: Optional[str] = None
    assessment_template_id: Optional[str] = None


class AnswerSubmissionRequest(BaseModel):
    question_id: str
    answer_text: str


class GradingSubmissionRequest(BaseModel):
    pass


async def call_ai_service(endpoint: str, payload: dict) -> dict:
    url = f"{settings.AI_SERVICE_URL}{endpoint}"
    timeout = httpx.Timeout(settings.AI_SERVICE_TIMEOUT_SECONDS)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            if endpoint == "/grade-assessment":
                resp = await client.post(url, params={"assessment_id": payload["assessment_id"]})
            else:
                resp = await client.post(url, json=payload)
    except httpx.TimeoutException as exc:
        logger.error("AI service timed out from %s after %ss", endpoint, settings.AI_SERVICE_TIMEOUT_SECONDS)
        raise HTTPException(
            504,
            "AI service timed out while generating or grading the assessment. Please try again.",
        ) from exc
    except httpx.HTTPError as exc:
        logger.error("AI service connection failed from %s: %s", endpoint, exc)
        raise HTTPException(502, "AI service unavailable. Check that the AI service is running.") from exc

    if resp.status_code != 200:
        logger.error("AI service error from %s: %s", endpoint, resp.text)
        raise HTTPException(502, f"AI service unavailable: {resp.text}")
    return resp.json()


def resolve_issuer(db: Session, identifier: str) -> Issuer:
    issuer= (
        db.query(Issuer)
        .filter(
            (Issuer.did == identifier)
            | (Issuer.wallet_address == identifier)
            | (Issuer.name == identifier)
        )
        .first()
    )
    if not issuer:
        raise HTTPException(404, "Issuer not registered")
    return issuer


def resolve_learner(db: Session, identifier: str) -> Learner:
    filters = [Learner.did == identifier, Learner.wallet_address == identifier]
    if identifier.isdigit():
        filters.append(Learner.id == int(identifier))

    learner = db.query(Learner).filter(filters[0] | filters[1] | filters[-1]).first()
    if not learner:
        raise HTTPException(404, "Learner not registered")
    return learner


@router.post("/materials/ingest")
async def ingest_material(req: MaterialIngestionRequest, db: Session = Depends(get_db)):
    issuer= resolve_issuer(db, req.issuer_id)

    try:
        ai_result = await call_ai_service("/ingest-material", {
            "issuer_id": issuer.did,
            "programme": req.programme,
            "title": req.title,
            "content": req.content,
            "difficulty_level": req.difficulty_level,
            "topics": req.topics or [],
        })

        material_id = ai_result["material_id"]
        material = Material(
            material_id=material_id,
            issuer_id=issuer.id,
            issuer_did=issuer.did,
            programme=req.programme,
            title=req.title,
            content=req.content,
            difficulty_level=req.difficulty_level,
            topics=json.dumps(req.topics or []),
            key_concepts=json.dumps(ai_result.get("key_concepts", [])),
            created_at=datetime.now(timezone.utc),
        )
        db.add(material)
        db.add(AuditLog(
            event_type=EventTypeEnum.MATERIAL_INGESTED,
            actor_did=issuer.did,
            target_id=material_id,
            detail=json.dumps({"title": req.title, "programme": req.programme}),
            created_at=datetime.now(timezone.utc),
        ))
        db.commit()

        return {
            "status": "success",
            "material_id": material_id,
            "issuer_id": issuer.did,
            "programme": req.programme,
            "title": req.title,
            "key_concepts": ai_result.get("key_concepts", []),
            "created_at": material.created_at.isoformat(),
            "ready_for_assessment": True,
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("Material ingestion failed")
        raise HTTPException(500, f"Material ingestion failed: {exc}")


@router.post("/create")
async def create_assessment(req: AssessmentCreationRequest, db: Session = Depends(get_db)):
    learner = resolve_learner(db, req.learner_id)
    template = None
    material = None

    if req.assessment_template_id:
        template = db.query(AssessmentTemplate).filter_by(
            assessment_template_id=req.assessment_template_id,
            status="ACTIVE",
        ).first()
        if not template:
            raise HTTPException(404, "Assessment template not found")
        enrolled = db.query(CourseEnrollment).filter_by(
            course_id=template.course_id,
            learner_id=learner.id,
        ).first()
        if not enrolled:
            raise HTTPException(403, "Course enrollment required")
        material = template.material
    elif req.material_id:
        material = db.query(Material).filter(Material.material_id == req.material_id).first()
    else:
        raise HTTPException(400, "assessment_template_id is required")

    if not material:
        raise HTTPException(404, "Material not found")

    try:
        difficulty = random.choice(["easy", "medium", "hard"])
        ai_result = await call_ai_service("/create-assessment", {
            "material_id": material.material_id,
            "student_id": learner.did,
            "num_questions": 30,
            "difficulty": difficulty,
        })

        assessment_id = ai_result["assessment_id"]
        questions = ai_result.get("internal_questions") or ai_result["questions"]
        learner_questions = ai_result["questions"]

        assessment = Assessment(
            assessment_id=assessment_id,
            learner_id=learner.id,
            issuer_id=material.issuer_id,
            course_id=template.course_id if template else None,
            assessment_template_id=template.id if template else None,
            material_db_id=material.id,
            material_id=material.material_id,
            programme=material.programme,
            difficulty_level=difficulty,
            questions_json=json.dumps(questions),
            answers_json=json.dumps([]),
            status="IN_PROGRESS",
            outcome=OutcomeEnum.PENDING,
            created_at=datetime.now(timezone.utc),
        )
        db.add(assessment)
        db.add(AuditLog(
            event_type=EventTypeEnum.ASSESSMENT_CREATED,
            actor_did=learner.did,
            target_id=assessment_id,
            detail=json.dumps({
                "material_id": material.material_id,
                "assessment_template_id": template.assessment_template_id if template else None,
                "num_questions": 30,
                "difficulty": difficulty,
                "generation_method": ai_result.get("generation_method", "local_fallback"),
            }),
            created_at=datetime.now(timezone.utc),
        ))
        db.commit()

        return {
            "status": "success",
            "assessment_id": assessment_id,
            "material_title": template.title if template else material.title,
            "num_questions": len(learner_questions),
            "learner_id": learner.did,
            "assessment_template_id": template.assessment_template_id if template else None,
            "generation_method": ai_result.get("generation_method", "local_fallback"),
            "questions": [
                {
                    "question_id": q["question_id"],
                    "question": q["question"],
                    "type": q["type"],
                    "points": q["points"],
                }
                for q in learner_questions
            ],
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("Assessment creation failed")
        raise HTTPException(500, f"Assessment creation failed: {exc}")


@router.post("/{assessment_id}/answers/submit")
async def submit_answer(
    assessment_id: str,
    req: AnswerSubmissionRequest,
    db: Session = Depends(get_db),
):
    assessment = db.query(Assessment).filter(Assessment.assessment_id == assessment_id).first()
    if not assessment:
        raise HTTPException(404, "Assessment not found")
    if assessment.status != "IN_PROGRESS":
        raise HTTPException(400, f"Assessment is {assessment.status}, cannot submit answers")

    try:
        ai_result = await call_ai_service("/submit-answer", {
            "assessment_id": assessment_id,
            "question_id": req.question_id,
            "answer_text": req.answer_text,
        })

        current_answers = json.loads(assessment.answers_json or "[]")
        current_answers = [a for a in current_answers if a.get("question_id") != req.question_id]
        current_answers.append({
            "question_id": req.question_id,
            "answer_text": req.answer_text,
            "submitted_at": datetime.now(timezone.utc).isoformat(),
        })
        assessment.answers_json = json.dumps(current_answers)

        db.add(AuditLog(
            event_type=EventTypeEnum.ANSWER_SUBMITTED,
            actor_did=assessment.learner.did,
            target_id=assessment_id,
            detail=json.dumps({
                "question_id": req.question_id,
                "progress": ai_result.get("progress", "submitted"),
            }),
            created_at=datetime.now(timezone.utc),
        ))
        db.commit()

        return {
            "status": "success",
            "assessment_id": assessment_id,
            "question_id": req.question_id,
            "received": True,
            "progress": ai_result.get("progress", "submitted"),
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("Answer submission failed")
        raise HTTPException(500, f"Answer submission failed: {exc}")


@router.post("/{assessment_id}/grade")
async def grade_assessment(
    assessment_id: str,
    req: GradingSubmissionRequest,
    db: Session = Depends(get_db),
):
    assessment = db.query(Assessment).filter(Assessment.assessment_id == assessment_id).first()
    if not assessment:
        raise HTTPException(404, "Assessment not found")
    if assessment.status != "IN_PROGRESS":
        raise HTTPException(400, f"Assessment already {assessment.status}")

    try:
        grades = await call_ai_service("/grade-assessment", {"assessment_id": assessment_id})

        total_earned = grades.get("total_earned", 0)
        total_points = grades.get("total_points", 0)
        percentage = grades.get("percentage", 0.0)
        outcome_value = grades.get("outcome", "PASS" if grades.get("passed", False) else "FAIL")
        passed = outcome_value == "PASS"
        overall_feedback = grades.get("overall_feedback", "")
        detailed_results = grades.get("detailed_results", [])

        assessment.status = "COMPLETED"
        assessment.outcome = OutcomeEnum.PENDING if outcome_value == "PENDING_REVIEW" else (
            OutcomeEnum.PASS if passed else OutcomeEnum.FAIL
        )
        assessment.ai_score = percentage
        assessment.ai_determination = outcome_value
        assessment.ai_feedback = overall_feedback
        assessment.ai_detailed_results = json.dumps(detailed_results)
        assessment.is_anomaly = bool(grades.get("anomaly_detected", False))
        assessment.anomaly_flags = json.dumps({
            "competency_model_used": grades.get("competency_model_used", False),
            "anomaly_model_used": grades.get("anomaly_model_used", False),
            "assessment_report_hash": grades.get("assessment_report_hash"),
            "grading_method": grades.get("grading_method"),
            "generation_method": grades.get("generation_method"),
        })
        assessment.completed_at = datetime.now(timezone.utc)

        certificate_token_id = None
        certificate_tx_hash = None

        if passed:
            try:
                learner = assessment.learner
                issuer= assessment.issuer
                metadata = {
                    "assessment_id": assessment_id,
                    "learner_did": learner.did,
                    "issuer_did": issuer.did,
                    "programme": assessment.programme,
                    "material_id": assessment.material_id,
                    "score": percentage,
                    "passed": True,
                    "assessment_report_hash": grades.get("assessment_report_hash"),
                    "issued_at": datetime.now(timezone.utc).isoformat(),
                    "feedback": overall_feedback,
                }
                metadata_cid = await pin_json(metadata)
                cert_result = get_blockchain_service().issue_certificate(
                    learner_address=learner.wallet_address,
                    issuer_did=issuer.did,
                    metadata_cid=metadata_cid,
                    artefact_cid=assessment_id,
                    issuer_private_key=settings.DEPLOYER_PRIVATE_KEY,
                    issuer_id=issuer.id,
                )

                certificate_token_id = cert_result.get("token_id")
                certificate_tx_hash = cert_result.get("tx_hash")
                verification_code = generate_verification_code()
                verification_url = (
                    f"http://localhost:5173/?verify_token={certificate_token_id}"
                    f"&code={verification_code}"
                )
                pdf_bytes = build_certificate_pdf_bytes(
                    learner_wallet=learner.wallet_address,
                    issuer_name=issuer.name,
                    course_name=assessment.course.title if assessment.course else assessment.programme,
                    assessment_title=assessment.template.title if assessment.template else "Assessment",
                    score_percentage=percentage,
                    token_id=certificate_token_id,
                    verification_code=verification_code,
                    verification_url=verification_url,
                )
                pdf_cid = await pin_file(pdf_bytes, f"certificate-{certificate_token_id or assessment_id}.pdf")
                db.add(Certificate(
                    token_id=certificate_token_id,
                    assessment_id=assessment.id,
                    learner_id=learner.id,
                    issuer_id=issuer.id,
                    metadata_cid=metadata_cid,
                    artefact_cid=assessment_id,
                    tx_hash=certificate_tx_hash,
                    verification_code=verification_code,
                    pdf_cid=pdf_cid,
                    score_percentage=percentage,
                    issued_at=datetime.now(timezone.utc),
                ))
                db.add(AuditLog(
                    event_type=EventTypeEnum.CERTIFICATE_ISSUED,
                    actor_did=issuer.did,
                    target_id=assessment_id,
                    tx_hash=certificate_tx_hash,
                    detail=json.dumps({"token_id": certificate_token_id, "learner_did": learner.did}),
                    created_at=datetime.now(timezone.utc),
                ))
            except Exception as cert_error:
                logger.exception("Certificate issuance failed after passing grade")
                assessment.ai_determination = "PASS_NO_CERT"
                overall_feedback = (
                    f"{overall_feedback} Certificate issuance failed: {cert_error}"
                ).strip()
                assessment.ai_feedback = overall_feedback

        db.add(AuditLog(
            event_type=EventTypeEnum.ASSESSMENT_GRADED,
            actor_did=assessment.learner.did,
            target_id=assessment_id,
            detail=json.dumps({
                "percentage": percentage,
                "outcome": outcome_value,
                "passed": passed,
                "certificate_issued": passed and certificate_token_id is not None,
                "assessment_report_hash": grades.get("assessment_report_hash"),
            }),
            created_at=datetime.now(timezone.utc),
        ))
        db.commit()

        return {
            "status": "success",
            "assessment_id": assessment_id,
            "learner_id": assessment.learner.did,
            "material_id": assessment.material_id,
            "total_earned": total_earned,
            "total_points": total_points,
            "percentage": percentage,
            "outcome": outcome_value,
            "passed": passed,
            "overall_feedback": overall_feedback,
            "detailed_results": detailed_results,
            "competency_prediction": grades.get("competency_prediction"),
            "competency_model_used": grades.get("competency_model_used", False),
            "anomaly_detected": grades.get("anomaly_detected", False),
            "anomaly_model_used": grades.get("anomaly_model_used", False),
            "assessment_report": grades.get("assessment_report"),
            "assessment_report_hash": grades.get("assessment_report_hash"),
            "grading_method": grades.get("grading_method", "local_only"),
            "generation_method": grades.get("generation_method", "local_fallback"),
            "certificate_token_id": certificate_token_id,
            "certificate_tx_hash": certificate_tx_hash,
            "difficulty_used": assessment.difficulty_level,
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("Assessment grading failed")
        raise HTTPException(500, f"Assessment grading failed: {exc}")


@router.get("/{assessment_id}/result")
async def get_assessment_result(assessment_id: str, db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(Assessment.assessment_id == assessment_id).first()
    if not assessment:
        raise HTTPException(404, "Assessment not found")

    cert = db.query(Certificate).filter(Certificate.assessment_id == assessment.id).first()
    detailed_results = json.loads(assessment.ai_detailed_results or "[]")

    return {
        "status": "success",
        "assessment_id": assessment_id,
        "learner_id": assessment.learner.did,
        "material_id": assessment.material_id,
        "programme": assessment.programme,
        "percentage": assessment.ai_score,
        "outcome": assessment.ai_determination,
        "passed": assessment.ai_determination == "PASS",
        "overall_feedback": assessment.ai_feedback,
        "detailed_results": detailed_results,
        "difficulty_used": assessment.difficulty_level,
        "assessment_report_hash": (json.loads(assessment.anomaly_flags or "{}")).get("assessment_report_hash"),
        "grading_method": (json.loads(assessment.anomaly_flags or "{}")).get("grading_method"),
        "generation_method": (json.loads(assessment.anomaly_flags or "{}")).get("generation_method"),
        "anomaly_detected": assessment.is_anomaly,
        "certificate_token_id": cert.token_id if cert else None,
        "certificate_tx_hash": cert.tx_hash if cert else None,
        "certificate_pdf_cid": cert.pdf_cid if cert else None,
        "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None,
    }
