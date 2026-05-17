"""
app/api/certificates.py — Certificate verification and revocation

GET  /certificates/{token_id}/verify   — public on-chain verification (FR-06)
POST /certificates/{token_id}/revoke   — institution revocation (FR-07)
GET  /certificates/learner/{did}       — get all certificates for a learner
"""
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.assessments import get_db
from app.core.config import get_settings
from app.models.db import Certificate, Institution, AuditLog, EventTypeEnum
from app.services.blockchain import get_blockchain_service

log = logging.getLogger("api.certificates")
router = APIRouter(prefix="/certificates", tags=["certificates"])


class RevokeRequest(BaseModel):
    institution_wallet: str
    reason: str


# ── Verification (FR-06) — public, no auth ───────────────────────────────────

@router.get("/{token_id}/verify")
async def verify_certificate(token_id: int, db: Session = Depends(get_db)):
    """
    FR-06: Public certificate verification.
    Queries Arbitrum blockchain directly — no backend auth required.
    Also enriches with off-chain record details where available.
    """
    chain = get_blockchain_service()

    # On-chain query (gas-free view call)
    try:
        on_chain = chain.verify_certificate(token_id)
    except Exception as e:
        log.error(f"Blockchain query failed: {e}")
        raise HTTPException(503, "Blockchain query failed. Check RPC connection.")

    # Enrich with off-chain data
    cert = db.query(Certificate).filter_by(token_id=token_id).first()

    # Log the verification query
    db.add(AuditLog(
        event_type = EventTypeEnum.VERIFICATION_QUERIED,
        target_id  = str(token_id),
        detail     = json.dumps({"valid": on_chain["valid"]})
    ))
    db.commit()

    return {
        "token_id":        token_id,
        "valid":           on_chain["valid"],
        "metadata_cid":    on_chain["meta_cid"],
        "artefact_cid":    on_chain["artefact_cid"],
        "institution_did": on_chain["institution_did"],
        "issued_at":       on_chain["timestamp"],
        # Off-chain enrichment (null if not in local DB)
        "programme":       cert.assessment.learner.programme if cert else None,
        "institution_name": cert.institution.name if cert else None,
        "tx_hash":         cert.tx_hash if cert else None,
        "is_revoked":      cert.is_revoked if cert else not on_chain["valid"],
        "revocation_reason": cert.revocation_reason if cert else None,
    }


# ── Revocation (FR-07) ───────────────────────────────────────────────────────

@router.post("/{token_id}/revoke")
async def revoke_certificate(
    token_id: int,
    req: RevokeRequest,
    db: Session = Depends(get_db),
):
    """
    FR-07: Institution revokes a certificate.
    Token stays on-chain with isRevoked=true for audit trail.
    """
    settings = get_settings()

    # Verify institution exists and is authorised
    institution = db.query(Institution).filter_by(
        wallet_address=req.institution_wallet
    ).first()
    if not institution:
        raise HTTPException(404, "Institution not registered")

    chain = get_blockchain_service()
    if not chain.is_authorised_issuer(req.institution_wallet):
        raise HTTPException(403, "Institution not authorised on-chain")

    # Check local record
    cert = db.query(Certificate).filter_by(token_id=token_id).first()
    if cert and cert.is_revoked:
        raise HTTPException(400, "Certificate already revoked")

    # Send revocation tx
    try:
        result = chain.revoke_certificate(
            token_id           = token_id,
            reason             = req.reason,
            issuer_private_key = settings.DEPLOYER_PRIVATE_KEY,
        )
    except Exception as e:
        log.error(f"Revocation failed: {e}")
        raise HTTPException(500, f"Blockchain revocation failed: {str(e)}")

    # Update local record
    if cert:
        cert.is_revoked        = True
        cert.revoked_at        = datetime.now(timezone.utc)
        cert.revocation_reason = req.reason

    db.add(AuditLog(
        event_type = EventTypeEnum.CERTIFICATE_REVOKED,
        actor_did  = institution.did,
        target_id  = str(token_id),
        tx_hash    = result.get("tx_hash"),
        detail     = json.dumps({"reason": req.reason})
    ))
    db.commit()

    return {
        "token_id": token_id,
        "revoked":  True,
        "tx_hash":  result.get("tx_hash"),
        "reason":   req.reason,
    }


# ── Learner certificate history ──────────────────────────────────────────────

@router.get("/learner/{learner_did}")
async def get_learner_certificates(learner_did: str, db: Session = Depends(get_db)):
    """Get all certificates for a learner DID."""
    from app.models.db import Learner
    learner = db.query(Learner).filter_by(did=learner_did).first()
    if not learner:
        raise HTTPException(404, "Learner not found")

    certs = db.query(Certificate).filter_by(learner_id=learner.id).all()
    return {
        "learner_did": learner_did,
        "certificates": [
            {
                "token_id":    c.token_id,
                "programme":   c.assessment.learner.programme,
                "institution": c.institution.name,
                "issued_at":   c.issued_at.isoformat() if c.issued_at else None,
                "is_revoked":  c.is_revoked,
                "tx_hash":     c.tx_hash,
                "metadata_cid": c.metadata_cid,
            }
            for c in certs
        ]
    }