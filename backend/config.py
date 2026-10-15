"""
Configuration for Enigma Backend.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME: str = "Enigma Incident Root-Cause Engine"
    API_V1_PREFIX: str = "/api"
    SANDBOX_REPO: str = os.getenv("SANDBOX_REPO", "enigma-sandbox/opentelemetry-demo")
    GITHUB_TOKEN: str | None = os.getenv("GITHUB_TOKEN", None)
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY", None)
    DEFAULT_INVITE_CODE: str = os.getenv("JUDGE_INVITE_CODE", "ENIGMA-GCP-2026")
    DEFAULT_MODE: str = os.getenv("DEFAULT_MODE", "live")


settings = Settings()
