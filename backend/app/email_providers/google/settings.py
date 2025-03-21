import os
from pathlib import Path
import secrets


BASE_DIR = Path(__file__).resolve().parent.parent

# Configuration Gmail
GOOGLE_CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials", "client_secret.json")

# Répertoire pour stocker les tokens d'authentification
TOKEN_DIR = os.path.join(BASE_DIR, "secure_storage", "tokens")

# Répertoire pour stocker les données temporaires
TEMP_STORAGE_DIR = os.path.join(BASE_DIR, "secure_storage", "temp_data")

# Répertoire pour les outputs
OUTPUT_DIR = os.path.join(BASE_DIR, "secure_storage", "tokens")


GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]
OAUTH_REDIRECT_URI = "http://localhost:8000/auth/callback"



SESSION_SECRET_KEY = os.environ.get("SESSION_SECRET_KEY", secrets.token_hex(32))

# S'assurer que les répertoires existent
os.makedirs(os.path.dirname(GOOGLE_CREDENTIALS_PATH), exist_ok=True)
os.makedirs(TOKEN_DIR, exist_ok=True)
os.makedirs(TEMP_STORAGE_DIR, exist_ok=True)
