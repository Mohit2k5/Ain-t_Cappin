import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load .env file from backend root or parent if present
backend_root = Path(__file__).resolve().parent.parent.parent
env_path = backend_root / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()


class Settings(BaseModel):
    PROJECT_NAME: str = "Ain't Cappin API"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "AI-powered fact-checking service using RAG and multi-perspective verification."
    ENVIRONMENT: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    PORT: int = Field(default_factory=lambda: int(os.getenv("PORT", "8000")))

    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv(
                "ALLOWED_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000",
            ).split(",")
            if origin.strip()
        ]
    )

    # API Keys
    TAVILY_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("TAVILY_API_KEY"))
    SERPAPI_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("SERPAPI_API_KEY"))
    GEMINI_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY"))
    GROQ_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("GROQ_API_KEY"))
    OPENAI_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))

    # Embedding & Memory Optimization
    USE_LIGHTWEIGHT_EMBEDDINGS: bool = Field(
        default_factory=lambda: os.getenv("USE_LIGHTWEIGHT_EMBEDDINGS", "true").lower() in ("true", "1", "yes")
    )

    # Claim Constraints
    MIN_CLAIM_LENGTH: int = 3
    MAX_CLAIM_LENGTH: int = 1000
    REQUEST_TIMEOUT_SECONDS: int = 45


settings = Settings()
