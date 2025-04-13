from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database Info
    MONGO_URI: str = "mongodb+srv://lxc3001:3kHtjRDURuw6CDmU@accorddb.q5v36.mongodb.net/"    # Connect to MongoDB （MongoDB connection string)
    DB_NAME: str = "accord"    # Name of collection
    JWT_SECRET: str = "your-secret-key"
    JWT_ALGORITHM: str = "HS256"

    # Microsoft Info
    MICROSOFT_CLIENT_ID: str = "dummy_client_id"
    MICROSOFT_CLIENT_SECRET: str = "dummy_secret"
    MICROSOFT_TENANT_ID: str = "common"
    REDIRECT_URI: str = "http://localhost:8000/api/auth/outlook/callback"
    
    # Google Info
    GMAIL_CLIENT_ID: str = "dummy_gmail_id"
    GMAIL_CLIENT_SECRET: str = "dummy_gmail_secret"
    GMAIL_REDIRECT_URI: str = "http://localhost:8000/api/auth/gmail/callback"
    
    # Email service settings
    EMAIL_SYNC_INTERVAL: int = 300  # Intervalle en secondes pour la synchronisation des emails

    # Demo mode
    IS_DEMO: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()

