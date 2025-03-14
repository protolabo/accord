from beanie import Document
from pydantic import Field
from datetime import datetime

class User(Document):
    username: str = Field(unique=True)
    email: str = Field(unique=True)
    password_hash: str
    created_at: datetime = datetime.now()

    class Settings:
        name = "users"
        indexes = [
            # Index
            "username", 
            # Complex index
            [("email", 1), ("created_at", -1)],
            # text index
            [("$**", "text")]  # search for text
        ]

class Email(Document):
    user_id: str
    subject: str
    content: str
    received_at: datetime = datetime.now()

    class Settings:
        name = "emails"
        indexes = [
            [("user_id", 1), ("received_at", -1)],
            [("subject", "text")]
        ]