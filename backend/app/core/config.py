"""
app/core/config.py — centralised settings loaded from .env
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "SkillCert Backend"
    DEBUG: bool   = False
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"

    # Database
    DATABASE_URL: str = "postgresql://skillcert:skillcert@localhost:5432/skillcert"

    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    # AI microservice
    AI_SERVICE_URL: str = "http://localhost:8001"

    # Blockchain — Arbitrum
    ARBITRUM_RPC_URL: str = "https://arb-sepolia.g.alchemy.com/v2/YOUR_KEY"
    REGISTRY_CONTRACT_ADDRESS: str = "0x0000000000000000000000000000000000000000"
    NFT_CONTRACT_ADDRESS: str      = "0x0000000000000000000000000000000000000000"
    DEPLOYER_PRIVATE_KEY: str      = "0x0000000000000000000000000000000000000000"

    # IPFS / Pinata
    PINATA_API_KEY: str    = ""
    PINATA_API_SECRET: str = ""
    PINATA_JWT: str        = ""

    # CORS — add your frontend origin
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()