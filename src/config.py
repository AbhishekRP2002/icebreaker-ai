"""
Configuration settings for the Icebreaker AI application
"""
import os
from typing import Optional


class Config:
    """Application configuration"""

    # Anthropic API settings
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL: str = os.getenv(
        "ANTHROPIC_MODEL", "claude-3-sonnet-20240229")

    # Google AI settings
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    GOOGLE_MODEL: str = os.getenv("GOOGLE_MODEL", "gemini-pro")

    # OpenAI settings (if needed)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")

    # Database settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "sqlite:///db/resume_data.db")

    # Email generation settings
    DEFAULT_EMAIL_TONE: str = "friendly"
    DEFAULT_EMAIL_TYPE: str = "simple"
    MAX_EMAIL_LENGTH: int = 250
    MAX_SUBJECT_LENGTH: int = 60

    # External API settings (for future implementation)
    GITHUB_API_TOKEN: Optional[str] = os.getenv("GITHUB_API_TOKEN")
    LINKEDIN_API_KEY: Optional[str] = os.getenv("LINKEDIN_API_KEY")
    LINKEDIN_API_SECRET: Optional[str] = os.getenv("LINKEDIN_API_SECRET")

    # Web scraping settings
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    REQUEST_TIMEOUT: int = 30

    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is present"""
        required_keys = [
            "ANTHROPIC_API_KEY",
        ]

        missing_keys = []
        for key in required_keys:
            if not getattr(cls, key):
                missing_keys.append(key)

        if missing_keys:
            print(
                f"Missing required environment variables: {', '.join(missing_keys)}")
            print(
                "Please set these environment variables before running the application.")
            return False

        return True

    @classmethod
    def get_model_config(cls, model_type: str = "anthropic") -> dict:
        """Get model configuration based on type"""
        if model_type == "anthropic":
            return {
                "api_key": cls.ANTHROPIC_API_KEY,
                "model": cls.ANTHROPIC_MODEL,
                "temperature": 0.7
            }
        elif model_type == "google":
            return {
                "api_key": cls.GOOGLE_API_KEY,
                "model": cls.GOOGLE_MODEL,
                "temperature": 0.7
            }
        elif model_type == "openai":
            return {
                "api_key": cls.OPENAI_API_KEY,
                "model": cls.OPENAI_MODEL,
                "temperature": 0.7
            }
        else:
            raise ValueError(f"Unsupported model type: {model_type}")


# Global config instance
config = Config()
