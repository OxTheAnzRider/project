"""
app/services/blockchain.py — Web3 interactions with Arbitrum

Handles:
  - Contract ABI loading
  - Certificate issuance (send tx)
  - Certificate revocation (send tx)
  - Certificate verification (call, no gas)
  - Issuer authorisation check
"""
import json
import logging
import os
from typing import Optional

from web3 import Web3
try:
    from web3.middleware import ExtraDataToPOAMiddleware
except ImportError:
    from web3.middleware import geth_poa_middleware as ExtraDataToPOAMiddleware

from app.core.config import get_settings
from app.services.key_manager import get_key_manager

log = logging.getLogger("blockchain")

# ── ABI definitions (inlined — copy from forge output/CertificationRegistry.sol/*.json) ──

REGISTRY_ABI = [
    {
        "inputs": [
            {"name": "learner",              "type": "address"},
            {"name": "issuerDID",       "type": "string"},
            {"name": "metadataCID",          "type": "string"},
            {"name": "assessmentCID",         "type": "string"},
        ],
        "name": "issueCertificate",
        "outputs": [{"name": "tokenId", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "tokenId", "type": "uint256"},
            {"name": "reason",  "type": "string"},
        ],
        "name": "revokeCertificate",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"name": "tokenId", "type": "uint256"}],
        "name": "verifyCertificate",
        "outputs": [
            {"name": "valid",          "type": "bool"},
            {"name": "metaCID",        "type": "string"},
            {"name": "assessmentArtefactCID", "type": "string"},
            {"name": "issuerDID_","type": "string"},
            {"name": "timestamp",      "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "isAuthorizedIssuer",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True,  "name": "tokenId",        "type": "uint256"},
            {"indexed": True,  "name": "learner",         "type": "address"},
            {"indexed": False, "name": "issuerDID",  "type": "string"},
            {"indexed": False, "name": "metadataCID",     "type": "string"},
            {"indexed": False, "name": "assessmentArtefactCID", "type": "string"},
            {"indexed": False, "name": "timestamp",       "type": "uint256"},
        ],
        "name": "CertificateIssued",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True,  "name": "tokenId",   "type": "uint256"},
            {"indexed": True,  "name": "revokedBy", "type": "address"},
            {"indexed": False, "name": "reason",    "type": "string"},
            {"indexed": False, "name": "timestamp", "type": "uint256"},
        ],
        "name": "CertificateRevoked",
        "type": "event",
    },
]


class BlockchainService:
    def __init__(self):
        settings = get_settings()
        self.w3  = Web3(Web3.HTTPProvider(settings.ARBITRUM_RPC_URL))
        # Arbitrum uses PoA — add middleware for ExtraData field
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

        self.registry = self.w3.eth.contract(
            address=Web3.to_checksum_address(settings.REGISTRY_CONTRACT_ADDRESS),
            abi=REGISTRY_ABI,
        )
        self.deployer_account = self.w3.eth.account.from_key(settings.DEPLOYER_PRIVATE_KEY)
        log.info(f"Blockchain service connected. Chain ID: {self.w3.eth.chain_id}")

    def is_connected(self) -> bool:
        return self.w3.is_connected()

    # ── Read-only ─────────────────────────────────────────────────────────

    def verify_certificate(self, token_id: int) -> dict:
        """
        Gas-free on-chain verification.
        Returns validity, metadata CID, artefact CID, issuerDID, timestamp.
        """
        result = self.registry.functions.verifyCertificate(token_id).call()
        valid, meta_cid, artefact_cid, issuer_did, timestamp = result
        return {
            "valid":           valid,
            "meta_cid":        meta_cid,
            "artefact_cid":    artefact_cid,
            "issuer_did": issuer_did,
            "timestamp":       timestamp,
        }

    def is_authorised_issuer(self, address: str) -> bool:
        return self.registry.functions.isAuthorizedIssuer(
            Web3.to_checksum_address(address)
        ).call()

    # ── Transactions ──────────────────────────────────────────────────────

    def issue_certificate(
        self,
        learner_address: str,
        issuer_did: str,
        metadata_cid: str,
        artefact_cid: str,
        issuer_private_key: str | None = None,
        issuer_id: int | None = None,
    ) -> dict:
        """
        Invoke issueCertificate on the registry.
        Returns tx_hash and token_id extracted from the event log.
        """
        if issuer_id is not None:
            managed = get_key_manager().get_key(issuer_id)
            if managed:
                _, issuer_private_key = managed
        if not issuer_private_key:
            issuer_private_key = get_settings().DEPLOYER_PRIVATE_KEY
        account = self.w3.eth.account.from_key(issuer_private_key)
        nonce   = self.w3.eth.get_transaction_count(account.address)

        tx = self.registry.functions.issueCertificate(
            Web3.to_checksum_address(learner_address),
            issuer_did,
            metadata_cid,
            artefact_cid,
        ).build_transaction({
            "chainId": self.w3.eth.chain_id,
            "from":    account.address,
            "nonce":   nonce,
            "gas":     200_000,
            "gasPrice": self.w3.eth.gas_price,
        })

        signed = self.w3.eth.account.sign_transaction(tx, issuer_private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        # Extract tokenId from CertificateIssued event
        token_id = None
        try:
            logs = self.registry.events.CertificateIssued().process_receipt(receipt)
            if logs:
                token_id = logs[0]["args"]["tokenId"]
        except Exception as e:
            log.warning(f"Could not parse event log: {e}")

        log.info(f"Certificate issued. tx={tx_hash.hex()} tokenId={token_id}")
        return {
            "tx_hash":  tx_hash.hex(),
            "token_id": token_id,
            "status":   receipt["status"],  # 1 = success
        }

    def revoke_certificate(
        self,
        token_id: int,
        reason: str,
        issuer_private_key: str,
    ) -> dict:
        account = self.w3.eth.account.from_key(issuer_private_key)
        nonce   = self.w3.eth.get_transaction_count(account.address)

        tx = self.registry.functions.revokeCertificate(token_id, reason).build_transaction({
            "chainId":  self.w3.eth.chain_id,
            "from":     account.address,
            "nonce":    nonce,
            "gas":      100_000,
            "gasPrice": self.w3.eth.gas_price,
        })

        signed  = self.w3.eth.account.sign_transaction(tx, issuer_private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        log.info(f"Certificate revoked. tokenId={token_id} tx={tx_hash.hex()}")
        return {
            "tx_hash": tx_hash.hex(),
            "status":  receipt["status"],
        }


# Singleton
_blockchain_service: Optional[BlockchainService] = None

def get_blockchain_service() -> BlockchainService:
    global _blockchain_service
    if _blockchain_service is None:
        _blockchain_service = BlockchainService()
    return _blockchain_service
