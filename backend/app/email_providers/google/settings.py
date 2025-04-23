import os
import secrets
from pathlib import Path


class Config:
    BASE_DIR =  Path(__file__).resolve().parent.parent.parent.parent

    # Configuration Google
    GOOGLE_CREDENTIALS_PATH = os.environ.get(
        "GOOGLE_CREDENTIALS_PATH",
        str(BASE_DIR / "app" / "email_providers" / "google" / "credentials.json")
    )

    TOKEN_DIR = os.environ.get(
        "GOOGLE_TOKEN_DIR",
        str(BASE_DIR / "app" / "email_providers" / "google" / "tokens")
    )

    TEMP_STORAGE_DIR = BASE_DIR / "secure_storage" / "temp_data"
    OUTPUT_DIR = BASE_DIR / "secure_storage" / "tokens"

    OAUTH_REDIRECT_URI = os.environ.get(
        "GMAIL_REDIRECT_URI",
        "http://localhost:8000/api/auth/gmail/callback"
    )

    # Scopes requis pour Gmail
    GOOGLE_SCOPES = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.compose",
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "openid"
    ]

    SESSION_SECRET_KEY = os.environ.get("SESSION_SECRET_KEY", secrets.token_hex(32))

    @classmethod
    def ensure_directories(cls):
        # creation de repertoire
        os.makedirs(os.path.dirname(cls.GOOGLE_CREDENTIALS_PATH), exist_ok=True)
        os.makedirs(cls.TOKEN_DIR, exist_ok=True)
        os.makedirs(cls.TEMP_STORAGE_DIR, exist_ok=True)
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)