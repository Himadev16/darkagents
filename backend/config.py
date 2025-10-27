"""
DARKAGENTS Configuration
Centralized configuration management using Pydantic Settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "DARKAGENTS"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./darkagents.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # OpenRouter API (for Claude access)
    OPENROUTER_API_KEY: str

    # JWT Authentication
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30

    # Agent Configuration
    DEFAULT_AGENT_TEMPERATURE: float = 0.5
    MAX_TOKENS_PER_AGENT: int = 200000
    AGENT_TIMEOUT_SECONDS: int = 600

    # Claude API Settings
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"  # Claude Sonnet 4.5
    CLAUDE_MAX_RETRIES: int = 3
    CLAUDE_TIMEOUT: int = 300

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
