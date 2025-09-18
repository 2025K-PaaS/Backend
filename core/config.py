# core/config.py

from typing import List, Any
from pydantic import Field, AliasChoices, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # .env 
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,  
        extra="ignore",       
    )

    # Database
    DATABASE_URL: str = Field(
        ...,
        validation_alias=AliasChoices("DATABASE_URL", "database_url"),
    )

    # JWT 
    JWT_SECRET: str = Field(
        "dev-secret",
        validation_alias=AliasChoices("JWT_SECRET", "jwt_secret"),
    )
    JWT_ALGORITHM: str = Field(
        "HS256",
        validation_alias=AliasChoices("JWT_ALGORITHM", "jwt_algorithm"),
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        60,
        validation_alias=AliasChoices("ACCESS_TOKEN_EXPIRE_MINUTES", "access_token_expire_minutes"),
    )

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000"],
        validation_alias=AliasChoices("CORS_ORIGINS", "cors_origins"),
    )

    # Admin
    ADMIN_API_KEY: str = Field(
        "dev-admin-key",
        validation_alias=AliasChoices("ADMIN_API_KEY", "admin_api_key"),
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _parse_cors_origins(cls, v: Any):
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("[") and s.endswith("]"):
                import json
                return json.loads(s)
            return [x.strip() for x in s.split(",") if x.strip()]
        return v

settings = Settings()
