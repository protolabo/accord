from beanie import Document
from datetime import datetime, timedelta
from pydantic import Field

class User(Document):
    microsoft_id: str = Field(unique=True)
    email: str
    outlook_tokens: dict
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "users"
        indexes = [
            "email",
            [("microsoft_id", 1)]
        ]

    @property
    def is_token_expired(self):
        return datetime.now() > self.outlook_tokens["expires_at"]

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





