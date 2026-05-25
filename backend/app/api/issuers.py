from datetime import datetime, timedelta, timezone
import csv
import io
import secrets
import string

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import current_user, get_db
from app.models.db import (
    Assessment,
    AssessmentTemplate,
    CodeStatusEnum,
    Course,
    CourseCode,
    CourseEnrollment,
    CourseStatusEnum,
    Issuer,
    Material,
    User,
)
from app.services.ipfs import pin_file
from app.services.key_manager import get_key_manager

router = APIRouter(prefix="/issuers", tags=["issuers"])


class CourseCreateRequest(BaseModel):
    title: str = Field(min_length=2)
    description: str = Field(min_length=5)
    status: CourseStatusEnum = CourseStatusEnum.ACTIVE


class CodeBatchRequest(BaseModel):
    count: int = Field(default=1, ge=1, le=500)
    quota: int = Field(default=1, ge=1, le=1000)
    expires_in_days: int | None = Field(default=30, ge=1, le=3650)


class TemplateCreateRequest(BaseModel):
    course_id: str
    title: str
    description: str | None = None
    material_id: str


class IssuerKeyRequest(BaseModel):
    address: str
    private_key: str


def require_issuer(user: User, db: Session) -> Issuer:
    issuer= None
    if user.issuer_id:
        issuer= db.query(Issuer).filter_by(id=user.issuer_id).first()
    if not issuer:
        issuer= db.query(Issuer).filter_by(wallet_address=user.wallet_address).first()
    if not issuer:
        raise HTTPException(403, "Issuer account required")
    return issuer


def code_value() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "SC-" + "".join(secrets.choice(alphabet) for _ in range(10))


def serialize_dt(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


@router.post("/courses")
async def create_course(
    req: CourseCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    issuer= require_issuer(user, db)
    course = Course(
        course_id=f"course_{int(datetime.now(timezone.utc).timestamp())}_{secrets.token_hex(3)}",
        issuer_id=issuer.id,
        title=req.title,
        description=req.description,
        status=req.status,
    )
    db.add(course)
    db.commit()
    return {
        "status": "success",
        "course_id": course.course_id,
        "title": course.title,
        "description": course.description,
    }


@router.get("/courses")
async def issuer_courses(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    issuer= require_issuer(user, db)
    courses = db.query(Course).filter_by(issuer_id=issuer.id).all()
    return {
        "courses": [
            {
                "course_id": c.course_id,
                "title": c.title,
                "description": c.description,
                "status": c.status.value,
                "created_at": serialize_dt(c.created_at),
                "enrollments": len(c.enrollments),
                "assessments": len(c.templates),
                "codes": [
                    {
                        "code": code.code,
                        "status": code.status.value,
                        "quota": code.quota,
                        "used_count": code.used_count,
                        "expires_at": serialize_dt(code.expires_at),
                        "created_at": serialize_dt(code.created_at),
                    }
                    for code in c.codes
                ],
                "materials": [
                    {
                        "material_id": template.material.material_id,
                        "title": template.material.title,
                        "programme": template.material.programme,
                    }
                    for template in c.templates
                    if template.material
                ],
                "templates": [
                    {
                        "assessment_template_id": template.assessment_template_id,
                        "title": template.title,
                        "material_id": template.material_id,
                        "programme": template.material.programme if template.material else None,
                        "created_at": serialize_dt(template.created_at),
                    }
                    for template in c.templates
                ],
            }
            for c in courses
        ]
    }


@router.post("/courses/{course_id}/codes")
async def generate_codes(
    course_id: str,
    req: CodeBatchRequest,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    issuer= require_issuer(user, db)
    course = db.query(Course).filter_by(course_id=course_id, issuer_id=issuer.id).first()
    if not course:
        raise HTTPException(404, "Course not found")

    expires_at = None
    if req.expires_in_days:
        # Store UTC-naive values because SQLite returns DateTime columns naive.
        expires_at = datetime.utcnow() + timedelta(days=req.expires_in_days)

    generated = []
    for _ in range(req.count):
        value = code_value()
        while db.query(CourseCode).filter_by(code=value).first():
            value = code_value()
        db.add(CourseCode(
            course_id=course.id,
            code=value,
            quota=req.quota,
            expires_at=expires_at,
            status=CodeStatusEnum.ACTIVE,
        ))
        generated.append(value)
    db.commit()
    return {"status": "success", "codes": generated}


@router.post("/courses/{course_id}/templates")
async def create_template(
    course_id: str,
    req: TemplateCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    issuer= require_issuer(user, db)
    course = db.query(Course).filter_by(course_id=course_id, issuer_id=issuer.id).first()
    if not course:
        raise HTTPException(404, "Course not found")
    material = db.query(Material).filter_by(material_id=req.material_id, issuer_id=issuer.id).first()
    if not material:
        raise HTTPException(404, "Material not found")

    template = AssessmentTemplate(
        assessment_template_id=f"tpl_{int(datetime.now(timezone.utc).timestamp())}_{secrets.token_hex(3)}",
        course_id=course.id,
        issuer_id=issuer.id,
        title=req.title,
        description=req.description,
        material_db_id=material.id,
        material_id=material.material_id,
        num_questions=30,
        status="ACTIVE",
    )
    db.add(template)
    db.commit()
    return {
        "status": "success",
        "assessment_template_id": template.assessment_template_id,
        "num_questions": 30,
    }


@router.post("/materials/upload")
async def upload_material_file(
    title: str = Form(...),
    programme: str = Form(...),
    course_id: str | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    issuer= require_issuer(user, db)
    if file.size and file.size > 50 * 1024 * 1024:
        raise HTTPException(400, "File exceeds 50MB limit")

    raw = await file.read()
    suffix = (file.filename or "").lower().rsplit(".", 1)[-1]
    if suffix not in {"txt", "pdf", "docx", "pptx"}:
        raise HTTPException(400, "Unsupported file type")

    text = ""
    if suffix == "txt":
        text = raw.decode("utf-8", errors="ignore")
    else:
        text = f"Preview extraction placeholder for {file.filename}. Install document extractors for full parsing."

    cid = await pin_file(raw, file.filename or "material")
    material = Material(
        material_id=f"mat_{int(datetime.now(timezone.utc).timestamp())}_{secrets.token_hex(3)}",
        issuer_id=issuer.id,
        issuer_did=issuer.did,
        programme=programme,
        title=title,
        content=text,
        difficulty_level="backend-controlled",
        topics="[]",
        key_concepts="[]",
    )
    db.add(material)
    db.commit()
    return {
        "status": "success",
        "material_id": material.material_id,
        "file_cid": cid,
        "extracted_text_preview": text[:2000],
    }


@router.get("/materials")
async def issuer_materials(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    issuer = require_issuer(user, db)
    materials = db.query(Material).filter_by(issuer_id=issuer.id).order_by(Material.created_at.desc()).all()
    return {
        "materials": [
            {
                "material_id": material.material_id,
                "title": material.title,
                "programme": material.programme,
                "topics": material.topics,
                "key_concepts": material.key_concepts,
                "created_at": serialize_dt(material.created_at),
            }
            for material in materials
        ]
    }


@router.get("/learners")
async def enrolled_learners(
    course_id: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    issuer= require_issuer(user, db)
    query = db.query(CourseEnrollment).join(Course).filter(Course.issuer_id == issuer.id)
    if course_id:
        query = query.filter(Course.course_id == course_id)
    enrollments = query.all()

    rows = []
    scores = []
    completed = 0
    for enrollment in enrollments:
        assessments = db.query(Assessment).filter_by(
            learner_id=enrollment.learner_id,
            course_id=enrollment.course_id,
        ).all()
        if not assessments:
            rows.append({
                "learner_wallet_address": enrollment.learner.wallet_address,
                "course_name": enrollment.course.title,
                "assessment_name": None,
                "score": None,
                "date_taken": None,
                "status": "NOT_STARTED",
            })
            continue
        for assessment in assessments:
            row_status = assessment.ai_determination or assessment.status
            if status and row_status != status:
                continue
            if assessment.ai_score is not None:
                scores.append(assessment.ai_score)
            if assessment.completed_at:
                completed += 1
            rows.append({
                "learner_wallet_address": assessment.learner.wallet_address,
                "course_name": enrollment.course.title,
                "assessment_name": assessment.template.title if assessment.template else None,
                "score": assessment.ai_score,
                "date_taken": assessment.completed_at.isoformat() if assessment.completed_at else None,
                "status": row_status,
            })

    return {
        "stats": {
            "total_learners": len({e.learner_id for e in enrollments}),
            "avg_score": round(sum(scores) / len(scores), 2) if scores else None,
            "completion_rate": round((completed / len(enrollments) * 100), 2) if enrollments else 0,
        },
        "learners": rows,
    }


@router.get("/learners/export")
async def export_enrolled_learners(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    data = await enrolled_learners(db=db, user=user)
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "learner_wallet_address", "course_name", "assessment_name", "score", "date_taken", "status"
    ])
    writer.writeheader()
    writer.writerows(data["learners"])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=skillcert-results.csv"},
    )


@router.post("/keys")
async def add_issuer_key(
    req: IssuerKeyRequest,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    issuer= require_issuer(user, db)
    get_key_manager().add_key(issuer.id, req.address, req.private_key)
    return {"status": "success", "address": req.address}


@router.post("/keys/revoke")
async def revoke_issuer_key(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    issuer= require_issuer(user, db)
    get_key_manager().revoke_key(issuer.id)
    return {"status": "success"}
