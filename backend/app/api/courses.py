from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
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
    Learner,
    User,
)

router = APIRouter(prefix="/courses", tags=["courses"])


def now_utc_naive() -> datetime:
    return datetime.utcnow()


class EnrollRequest(BaseModel):
    code: str


@router.get("")
async def list_courses(db: Session = Depends(get_db)):
    courses = db.query(Course).filter(Course.status == CourseStatusEnum.ACTIVE).all()
    return {
        "courses": [
            {
                "course_id": c.course_id,
                "title": c.title,
                "description": c.description,
                "institution": c.institution.name if c.institution else None,
                "status": c.status.value,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in courses
        ]
    }


@router.post("/enroll")
async def enroll_with_code(
    req: EnrollRequest,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    if not user.learner_id:
        raise HTTPException(403, "Only learners can enroll in courses")

    code = db.query(CourseCode).filter_by(code=req.code.strip().upper()).first()
    if not code or code.status != CodeStatusEnum.ACTIVE:
        raise HTTPException(404, "Code not found or inactive")
    if code.expires_at and code.expires_at < now_utc_naive():
        raise HTTPException(400, "Code expired")
    if code.used_count >= code.quota:
        raise HTTPException(400, "Code quota exceeded")

    existing = db.query(CourseEnrollment).filter_by(
        course_id=code.course_id,
        learner_id=user.learner_id,
    ).first()
    if existing:
        return {"status": "success", "message": "Already enrolled", "course_id": code.course.course_id}

    db.add(CourseEnrollment(
        course_id=code.course_id,
        learner_id=user.learner_id,
        code_id=code.id,
    ))
    code.used_count += 1
    if code.used_count >= code.quota:
        code.status = CodeStatusEnum.USED
    db.commit()
    return {
        "status": "success",
        "course_id": code.course.course_id,
        "title": code.course.title,
        "enrolled_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/mine")
async def my_courses(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    if not user.learner_id:
        raise HTTPException(403, "Only learners can view learner courses")
    enrollments = db.query(CourseEnrollment).filter_by(learner_id=user.learner_id).all()
    return {
        "courses": [
            {
                "course_id": e.course.course_id,
                "title": e.course.title,
                "description": e.course.description,
                "enrolled_at": e.enrolled_at.isoformat(),
                "assessments": [
                    {
                        "assessment_template_id": t.assessment_template_id,
                        "title": t.title,
                        "description": t.description,
                        "num_questions": t.num_questions,
                    }
                    for t in e.course.templates
                    if t.status == "ACTIVE"
                ],
            }
            for e in enrollments
        ]
    }


@router.get("/{course_id}/assessments")
async def course_assessments(
    course_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    course = db.query(Course).filter_by(course_id=course_id).first()
    if not course:
        raise HTTPException(404, "Course not found")
    enrolled = db.query(CourseEnrollment).filter_by(course_id=course.id, learner_id=user.learner_id).first()
    if not enrolled:
        raise HTTPException(403, "Enrollment required")
    return {
        "assessments": [
            {
                "assessment_template_id": t.assessment_template_id,
                "title": t.title,
                "description": t.description,
                "num_questions": 30,
            }
            for t in course.templates
            if t.status == "ACTIVE"
        ]
    }
