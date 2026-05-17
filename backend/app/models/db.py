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


# ── Institution ──────────────────────────────────────────────────────────────
class Institution(Base):
    __tablename__ = "institutions"

    id                    = Column(Integer, primary_key=True, index=True)
    did                   = Column(String(255), unique=True, index=True, nullable=False)
    name                  = Column(String(255), nullable=False)
    wallet_address        = Column(String(42), unique=True, nullable=False)
    accreditation_status  = Column(Boolean, default=True)
    created_at            = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    assessments  = relationship("Assessment", back_populates="institution")
    certificates = relationship("Certificate", back_populates="institution")
    materials    = relationship("Material", back_populates="institution")


# ── Learning Material ────────────────────────────────────────────────────────
class Material(Base):
    __tablename__ = "materials"

    id               = Column(Integer, primary_key=True, index=True)
    material_id      = Column(String(255), unique=True, index=True, nullable=False)
    institution_id   = Column(Integer, ForeignKey("institutions.id"), nullable=False)
    institution_did  = Column(String(255), nullable=False)
    programme        = Column(String(100), nullable=False)
    title            = Column(String(255), nullable=False)
    content          = Column(Text, nullable=False)
    difficulty_level = Column(String(50), default="intermediate")
    topics           = Column(Text, nullable=True)
    key_concepts     = Column(Text, nullable=True)
    created_at       = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    institution = relationship("Institution", back_populates="materials")
    assessments = relationship("Assessment", back_populates="material")


# ── Assessment ───────────────────────────────────────────────────────────────
class Assessment(Base):
    __tablename__ = "assessments"

    id              = Column(Integer, primary_key=True, index=True)
    assessment_id   = Column(String(255), unique=True, index=True, nullable=True)
    learner_id      = Column(Integer, ForeignKey("learners.id"), nullable=False)
    institution_id  = Column(Integer, ForeignKey("institutions.id"), nullable=False)
    material_db_id  = Column(Integer, ForeignKey("materials.id"), nullable=True)
    material_id     = Column(String(255), nullable=True)
    programme       = Column(String(100), nullable=True)
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
    adjudicated_by_id   = Column(Integer, ForeignKey("institutions.id"), nullable=True)
    adjudicated_at      = Column(DateTime, nullable=True)

    # Storage
    artefact_cid        = Column(String(255), nullable=True)  # IPFS CID of full artefact
    created_at          = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at        = Column(DateTime, nullable=True)

    learner     = relationship("Learner", back_populates="assessments")
    institution = relationship("Institution", back_populates="assessments", foreign_keys=[institution_id])
    material    = relationship("Material", back_populates="assessments")
    certificate = relationship("Certificate", back_populates="assessment", uselist=False)


# ── Certificate ──────────────────────────────────────────────────────────────
class Certificate(Base):
    __tablename__ = "certificates"

    id             = Column(Integer, primary_key=True, index=True)
    token_id       = Column(Integer, unique=True, nullable=True)   # on-chain tokenId
    learner_id     = Column(Integer, ForeignKey("learners.id"), nullable=False)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False)
    assessment_id  = Column(Integer, ForeignKey("assessments.id"), nullable=False)

    metadata_cid   = Column(String(255), nullable=True)   # IPFS CID of VC JSON
    artefact_cid   = Column(String(255), nullable=True)   # IPFS CID of assessment artefact
    tx_hash        = Column(String(66), nullable=True)     # Arbitrum transaction hash

    issued_at      = Column(DateTime, nullable=True)
    revoked_at     = Column(DateTime, nullable=True)
    revocation_reason = Column(Text, nullable=True)
    is_revoked     = Column(Boolean, default=False)

    learner     = relationship("Learner", back_populates="certificates")
    institution = relationship("Institution", back_populates="certificates")
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
