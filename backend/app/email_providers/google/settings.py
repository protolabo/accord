import os
from pathlib import Path
import secrets


BASE_DIR = Path(__file__).resolve().parent.parent

# Chemin vers le répertoire contenant les credentials Google
GOOGLE_CREDENTIALS_PATH = os.environ.get(
    "GOOGLE_CREDENTIALS_PATH",
    str(Path(__file__).parent / "credentials.json")
)

# Répertoire pour stocker les tokens
TOKEN_DIR = os.environ.get(
    "GOOGLE_TOKEN_DIR", 
    str(Path(__file__).parent / "tokens")
)

# Répertoire pour stocker les données temporaires
TEMP_STORAGE_DIR = os.path.join(BASE_DIR, "secure_storage", "temp_data")

# Répertoire pour les outputs
OUTPUT_DIR = os.path.join(BASE_DIR, "secure_storage", "tokens")

# URL de redirection pour l'authentification OAuth2
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
    "https://www.googleapis.com/auth/userinfo.profile"
]

SESSION_SECRET_KEY = os.environ.get("SESSION_SECRET_KEY", secrets.token_hex(32))

# S'assurer que les répertoires existent
os.makedirs(os.path.dirname(GOOGLE_CREDENTIALS_PATH), exist_ok=True)
os.makedirs(TOKEN_DIR, exist_ok=True)
os.makedirs(TEMP_STORAGE_DIR, exist_ok=True)
