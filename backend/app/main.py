"""
app/main.py — SkillCert Backend API
Port: 8000

Mounts:
  /api/assessments  — assessment submission and adjudication
  /api/certificates — verification and revocation
  /api/learners     — registration
  /api/issuers — registration and admin
  /api/audit        — audit log queries
  /health           — liveness
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api import assessments, auth, certificates, courses, issuers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
log = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    log.info(f"Starting {settings.APP_NAME}")
    try:
        from app.models.db import Base, engine
        Base.metadata.create_all(bind=engine)
        log.info("Database tables checked")
    except Exception as exc:
        log.warning(f"Database table check skipped: {exc}")
    yield
    log.info("Shutdown complete")


settings = get_settings()

app = FastAPI(
    title="SkillCert API",
    version="1.0.0",
    description="Anti-Forgery Certification Registry — Backend API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(assessments.router, prefix="/api")
app.include_router(certificates.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(courses.router, prefix="/api")
app.include_router(issuers.router, prefix="/api")


# ── Learner registration (inline for brevity) ────────────────────────────────
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import hashlib
from app.api.assessments import get_db

learner_router = APIRouter(prefix="/api/learners", tags=["learners"])

class RegisterLearnerRequest(BaseModel):
    full_name:      str
    email:          str
    wallet_address: str
    programme:      str

@learner_router.post("/register")
async def register_learner(req: RegisterLearnerRequest, db = Depends(get_db)):
    """FR-01: Register a learner with hashed PII."""
    from app.models.db import Learner

    hashed_name  = hashlib.sha256(req.full_name.encode()).hexdigest()
    hashed_email = hashlib.sha256(req.email.encode()).hexdigest()
    did = f"did:ethr:arbitrum:{req.wallet_address}"

    learner = db.query(Learner).filter_by(wallet_address=req.wallet_address).first()
    if learner:
        learner.programme = req.programme
        learner.hashed_name = hashed_name
        learner.hashed_email = hashed_email
    else:
        learner = Learner(
            did=did,
            hashed_name=hashed_name,
            hashed_email=hashed_email,
            wallet_address=req.wallet_address,
            programme=req.programme,
        )
        db.add(learner)
    db.commit()
    db.refresh(learner)

    return {
        "id":            learner.id,
        "did":           did,
        "wallet_address": req.wallet_address,
        "programme":     req.programme,
        "message":       "Learner registered. DID generated.",
    }

app.include_router(learner_router)


# ── Issuer registration (inline) ────────────────────────────────────────
inst_router = APIRouter(prefix="/api/issuers", tags=["issuers"])

class RegisterIssuerRequest(BaseModel):
    name:           str
    wallet_address: str

@inst_router.post("/register")
async def register_issuer(req: RegisterIssuerRequest, db = Depends(get_db)):
    """FR-02: Register an issuer and generate its DID."""
    from app.models.db import Issuer

    did = f"did:ethr:arbitrum:{req.wallet_address}"
    issuer= db.query(Issuer).filter_by(wallet_address=req.wallet_address).first()
    if issuer:
        issuer.name = req.name
        issuer.did = did
    else:
        issuer= Issuer(
            did=did,
            name=req.name,
            wallet_address=req.wallet_address,
        )
        db.add(issuer)
    db.commit()
    db.refresh(issuer)

    return {
        "id":            issuer.id,
        "did":           did,
        "name":          req.name,
        "wallet_address": req.wallet_address,
        "message":       "Issuer registered. Grant ISSUER_ROLE via the admin contract call.",
    }

@inst_router.get("/{wallet}/pending-reviews")
async def pending_reviews(wallet: str):
    """Get assessments awaiting human adjudication for this issuer."""
    return {"issuer_wallet": wallet, "pending": []}

app.include_router(inst_router)


# ── Audit log ─────────────────────────────────────────────────────────────────
audit_router = APIRouter(prefix="/api/audit", tags=["audit"])

@audit_router.get("/")
async def get_audit_log(limit: int = 50, offset: int = 0):
    """FR-09: Return paginated audit log."""
    return {"events": [], "total": 0, "limit": limit, "offset": offset}

app.include_router(audit_router)


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    from app.services.blockchain import get_blockchain_service
    try:
        chain = get_blockchain_service()
        chain_ok = chain.is_connected()
    except Exception:
        chain_ok = False

    return {
        "status":    "ok",
        "chain":     chain_ok,
        "chain_id":  421614,  # Arbitrum Sepolia
    }
