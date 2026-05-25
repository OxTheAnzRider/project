"""
app/models/db.py — SQLAlchemy ORM models matching the Chapter 3 database design
"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean,
    DateTime, Text, ForeignKey, Enum, UniqueConstraint
)
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker
import enum

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class OutcomeEnum(str, enum.Enum):
    PASS    = "PASS"
    FAIL    = "FAIL"
    PENDING = "PENDING"      # awaiting human review


class EventTypeEnum(str, enum.Enum):
    REGISTRATION         = "REGISTRATION"
    MATERIAL_INGESTED    = "MATERIAL_INGESTED"
    ASSESSMENT_CREATED   = "ASSESSMENT_CREATED"
    ANSWER_SUBMITTED     = "ANSWER_SUBMITTED"
    ASSESSMENT_GRADED    = "ASSESSMENT_GRADED"
    ASSESSMENT_SUBMITTED = "ASSESSMENT_SUBMITTED"
    AI_EVALUATED         = "AI_EVALUATED"
    HUMAN_ADJUDICATED    = "HUMAN_ADJUDICATED"
    CERTIFICATE_ISSUED   = "CERTIFICATE_ISSUED"
    CERTIFICATE_REVOKED  = "CERTIFICATE_REVOKED"
    VERIFICATION_QUERIED = "VERIFICATION_QUERIED"
    COURSE_CREATED       = "COURSE_CREATED"
    COURSE_ENROLLED      = "COURSE_ENROLLED"
    CODE_GENERATED       = "CODE_GENERATED"


class UserRoleEnum(str, enum.Enum):
    LEARNER = "LEARNER"
    issuer= "issuer"
    ADMIN = "ADMIN"


class CodeStatusEnum(str, enum.Enum):
    ACTIVE = "ACTIVE"
    USED = "USED"
    REVOKED = "REVOKED"


class CourseStatusEnum(str, enum.Enum):
    ACTIVE = "ACTIVE"
    DRAFT = "DRAFT"
    ARCHIVED = "ARCHIVED"


# ── Auth ─────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    email         = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    wallet_address = Column(String(42), unique=True, nullable=False)
    role          = Column(Enum(UserRoleEnum), default=UserRoleEnum.LEARNER, nullable=False)
    learner_id    = Column(Integer, ForeignKey("learners.id"), nullable=True)
    issuer_id = Column(Integer, ForeignKey("issuers.id"), nullable=True)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=False)
    refresh_token_hash = Column(String(255), unique=True, nullable=False)
    created_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at    = Column(DateTime, nullable=False)
    revoked_at    = Column(DateTime, nullable=True)


# ── Learner ──────────────────────────────────────────────────────────────────
class Learner(Base):
    __tablename__ = "learners"

    id              = Column(Integer, primary_key=True, index=True)
    did             = Column(String(255), unique=True, index=True, nullable=False)
    hashed_name     = Column(String(255), nullable=False)      # SHA-256 of full name
    hashed_email    = Column(String(255), unique=True, nullable=False)
    wallet_address  = Column(String(42), unique=True, nullable=False)  # 0x...
    programme       = Column(String(100), nullable=False)
    created_at      = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active       = Column(Boolean, default=True)

    assessments  = relationship("Assessment", back_populates="learner")
    certificates = relationship("Certificate", back_populates="learner")


# ── issuer──────────────────────────────────────────────────────────────
class Issuer(Base):
    __tablename__ = "issuers"

    id                    = Column(Integer, primary_key=True, index=True)
    did                   = Column(String(255), unique=True, index=True, nullable=False)
    name                  = Column(String(255), nullable=False)
    wallet_address        = Column(String(42), unique=True, nullable=False)
    accreditation_status  = Column(Boolean, default=True)
    created_at            = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    assessments  = relationship("Assessment", back_populates="issuer", foreign_keys="Assessment.issuer_id")
    certificates = relationship("Certificate", back_populates="issuer")
    materials    = relationship("Material", back_populates="issuer")
    courses      = relationship("Course", back_populates="issuer")


# ── Learning Material ────────────────────────────────────────────────────────
class Material(Base):
    __tablename__ = "materials"

    id               = Column(Integer, primary_key=True, index=True)
    material_id      = Column(String(255), unique=True, index=True, nullable=False)
    issuer_id   = Column(Integer, ForeignKey("issuers.id"), nullable=False)
    issuer_did  = Column(String(255), nullable=False)
    programme        = Column(String(100), nullable=False)
    title            = Column(String(255), nullable=False)
    content          = Column(Text, nullable=False)
    difficulty_level = Column(String(50), default="intermediate")
    topics           = Column(Text, nullable=True)
    key_concepts     = Column(Text, nullable=True)
    created_at       = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    issuer= relationship("Issuer", back_populates="materials")
    assessments = relationship("Assessment", back_populates="material")
    templates   = relationship("AssessmentTemplate", back_populates="material")


# ── Courses and Enrollment ──────────────────────────────────────────────────
class Course(Base):
    __tablename__ = "courses"

    id             = Column(Integer, primary_key=True, index=True)
    course_id      = Column(String(255), unique=True, index=True, nullable=False)
    issuer_id = Column(Integer, ForeignKey("issuers.id"), nullable=False)
    title          = Column(String(255), nullable=False)
    description    = Column(Text, nullable=False)
    status         = Column(Enum(CourseStatusEnum), default=CourseStatusEnum.ACTIVE, nullable=False)
    created_at     = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    issuer= relationship("Issuer", back_populates="courses")
    codes       = relationship("CourseCode", back_populates="course")
    enrollments = relationship("CourseEnrollment", back_populates="course")
    templates   = relationship("AssessmentTemplate", back_populates="course")


class CourseCode(Base):
    __tablename__ = "course_codes"
    __table_args__ = (UniqueConstraint("code", name="uq_course_code"),)

    id             = Column(Integer, primary_key=True, index=True)
    course_id      = Column(Integer, ForeignKey("courses.id"), nullable=False)
    code           = Column(String(64), unique=True, index=True, nullable=False)
    status         = Column(Enum(CodeStatusEnum), default=CodeStatusEnum.ACTIVE, nullable=False)
    quota          = Column(Integer, default=1, nullable=False)
    used_count     = Column(Integer, default=0, nullable=False)
    expires_at     = Column(DateTime, nullable=True)
    created_at     = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    revoked_at     = Column(DateTime, nullable=True)

    course = relationship("Course", back_populates="codes")


class CourseEnrollment(Base):
    __tablename__ = "course_enrollments"
    __table_args__ = (UniqueConstraint("course_id", "learner_id", name="uq_course_learner"),)

    id             = Column(Integer, primary_key=True, index=True)
    course_id      = Column(Integer, ForeignKey("courses.id"), nullable=False)
    learner_id     = Column(Integer, ForeignKey("learners.id"), nullable=False)
    code_id        = Column(Integer, ForeignKey("course_codes.id"), nullable=True)
    enrolled_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    course = relationship("Course", back_populates="enrollments")
    learner = relationship("Learner")
    code_record = relationship("CourseCode")


class AssessmentTemplate(Base):
    __tablename__ = "assessment_templates"

    id             = Column(Integer, primary_key=True, index=True)
    assessment_template_id = Column(String(255), unique=True, index=True, nullable=False)
    course_id      = Column(Integer, ForeignKey("courses.id"), nullable=False)
    issuer_id = Column(Integer, ForeignKey("issuers.id"), nullable=False)
    title          = Column(String(255), nullable=False)
    description    = Column(Text, nullable=True)
    material_db_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    material_id    = Column(String(255), nullable=False)
    num_questions  = Column(Integer, default=30, nullable=False)
    status         = Column(String(30), default="ACTIVE", nullable=False)
    created_at     = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    course = relationship("Course", back_populates="templates")
    material = relationship("Material", back_populates="templates")


# ── Assessment ───────────────────────────────────────────────────────────────
class Assessment(Base):
    __tablename__ = "assessments"

    id              = Column(Integer, primary_key=True, index=True)
    assessment_id   = Column(String(255), unique=True, index=True, nullable=True)
    learner_id      = Column(Integer, ForeignKey("learners.id"), nullable=False)
    issuer_id  = Column(Integer, ForeignKey("issuers.id"), nullable=False)
    course_id       = Column(Integer, ForeignKey("courses.id"), nullable=True)
    assessment_template_id = Column(Integer, ForeignKey("assessment_templates.id"), nullable=True)
    material_db_id  = Column(Integer, ForeignKey("materials.id"), nullable=True)
    material_id     = Column(String(255), nullable=True)
    programme       = Column(String(100), nullable=True)
    difficulty_level = Column(String(50), nullable=True)
    questions_json  = Column(Text, nullable=True)
    answers_json    = Column(Text, nullable=True)
    status          = Column(String(30), default="IN_PROGRESS")

    # Rubric scores (1-5)
    rubric_technical    = Column(Float, nullable=True)
    rubric_practical    = Column(Float, nullable=True)
    rubric_safety       = Column(Float, nullable=True)
    rubric_problemsolve = Column(Float, nullable=True)
    rubric_professional = Column(Float, nullable=True)

    # Knowledge scores (0-1)
    know_foundations    = Column(Float, nullable=True)
    know_regulatory     = Column(Float, nullable=True)
    know_applied        = Column(Float, nullable=True)

    # Metadata
    attempts            = Column(Integer, default=1)
    days_before_end     = Column(Float, nullable=True)
    upload_lag_hours    = Column(Float, nullable=True)
    has_attestation     = Column(Boolean, default=False)
    attestation_cid     = Column(String(255), nullable=True)  # IPFS CID

    # AI outputs
    ai_score            = Column(Float, nullable=True)
    ai_confidence       = Column(Float, nullable=True)
    ai_determination    = Column(String(10), nullable=True)   # PASS / FAIL
    ai_feedback         = Column(Text, nullable=True)
    ai_detailed_results = Column(Text, nullable=True)
    shap_json           = Column(Text, nullable=True)         # JSON string
    is_anomaly          = Column(Boolean, default=False)
    anomaly_score       = Column(Float, nullable=True)
    anomaly_flags       = Column(Text, nullable=True)         # JSON list

    # Final outcome
    outcome             = Column(Enum(OutcomeEnum), default=OutcomeEnum.PENDING)
    adjudicated_by_id   = Column(Integer, ForeignKey("issuers.id"), nullable=True)
    adjudicated_at      = Column(DateTime, nullable=True)

    # Storage
    artefact_cid        = Column(String(255), nullable=True)  # IPFS CID of full artefact
    created_at          = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at        = Column(DateTime, nullable=True)

    learner     = relationship("Learner", back_populates="assessments")
    issuer= relationship("Issuer", back_populates="assessments", foreign_keys=[issuer_id])
    material    = relationship("Material", back_populates="assessments")
    course      = relationship("Course")
    template    = relationship("AssessmentTemplate")
    certificate = relationship("Certificate", back_populates="assessment", uselist=False)


# ── Certificate ──────────────────────────────────────────────────────────────
class Certificate(Base):
    __tablename__ = "certificates"

    id             = Column(Integer, primary_key=True, index=True)
    token_id       = Column(Integer, unique=True, nullable=True)   # on-chain tokenId
    learner_id     = Column(Integer, ForeignKey("learners.id"), nullable=False)
    issuer_id = Column(Integer, ForeignKey("issuers.id"), nullable=False)
    assessment_id  = Column(Integer, ForeignKey("assessments.id"), nullable=False)

    metadata_cid   = Column(String(255), nullable=True)   # IPFS CID of VC JSON
    artefact_cid   = Column(String(255), nullable=True)   # IPFS CID of assessment artefact
    tx_hash        = Column(String(66), nullable=True)     # Arbitrum transaction hash
    verification_code = Column(String(32), unique=True, index=True, nullable=True)
    pdf_cid        = Column(String(255), nullable=True)
    pdf_path       = Column(String(500), nullable=True)
    score_percentage = Column(Float, nullable=True)

    issued_at      = Column(DateTime, nullable=True)
    revoked_at     = Column(DateTime, nullable=True)
    revocation_reason = Column(Text, nullable=True)
    is_revoked     = Column(Boolean, default=False)

    learner     = relationship("Learner", back_populates="certificates")
    issuer= relationship("Issuer", back_populates="certificates")
    assessment  = relationship("Assessment", back_populates="certificate")


# ── Audit Log ────────────────────────────────────────────────────────────────
class AuditLog(Base):
    __tablename__ = "audit_log"

    id         = Column(Integer, primary_key=True, index=True)
    event_type = Column(Enum(EventTypeEnum), nullable=False)
    actor_did  = Column(String(255), nullable=True)
    target_id  = Column(String(255), nullable=True)   # learner DID / tokenId
    detail     = Column(Text, nullable=True)           # JSON detail blob
    tx_hash    = Column(String(66), nullable=True)     # null for off-chain events
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class IssuerKey(Base):
    __tablename__ = "issuer_keys"

    id                    = Column(Integer, primary_key=True, index=True)
    issuer_id         = Column(Integer, ForeignKey("issuers.id"), nullable=False)
    issuer_address    = Column(String(42), nullable=False)
    private_key_encrypted  = Column(Text, nullable=False)
    created_at             = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    revoked_at             = Column(DateTime, nullable=True)

    issuer= relationship("Issuer")
