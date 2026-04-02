"""
Configuration module for the LinkedIn Enhancement Tool.
Loads environment variables and defines application settings.
"""

import os
from dotenv import load_dotenv

# Force load .env from backend folder
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

class Config:
    """Application configuration class."""
    
    # Google Gemini API Key - Get yours at https://makersuite.google.com/app/apikey
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    # Flask settings
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    PORT = int(os.getenv("FLASK_PORT", 5000))
    
    # AI Model settings (default to a known available model from list_models response)
    # Use .env variable AI_MODEL to override if needed (e.g. gemini-2.5-flash, gemini-flash-lite-latest)
    AI_MODEL = os.getenv("AI_MODEL", "gemini-flash-lite-latest")
    MAX_TOKENS = 4096
    TEMPERATURE = 0.7  # Balance between creativity and consistency

    # LinkedIn profile provider settings
    # Provider-first mode uses an external profile data API before direct HTML fetch.
    LINKEDIN_FETCH_MODE = os.getenv("LINKEDIN_FETCH_MODE", "manual_only")
    LINKEDIN_PROVIDER = os.getenv("LINKEDIN_PROVIDER", "proxycurl").lower()
    PROXYCURL_API_KEY = os.getenv("PROXYCURL_API_KEY", "")
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        if not cls.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY not found! Please set it in your .env file.\n"
                "Get your free API key at: https://makersuite.google.com/app/apikey"
            )