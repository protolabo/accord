from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGO_URI: str = "mongodb+srv://lxc3001:3kHtjRDURuw6CDmU@accorddb.q5v36.mongodb.net/"    # Connect to MongoDB （MongoDB connection string)
    DB_NAME: str = "accord"    # Name of collection
    JWT_SECRET: str = "your-secret-key"
    JWT_ALGORITHM: str = "HS256"
    OUTLOOK_CLIENT_ID: str = ""
    OUTLOOK_CLIENT_SECRET: str = ""

    class Config:
        env_file = ".env"

settings = Settings()