from beanie import Document
from datetime import datetime, timedelta
from pydantic import Field
from pydantic import ConfigDict

class User(Document):
    microsoft_id: str = Field(json_schema_extra={"unique": True})
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
        return datetime.now() > self.user.outlook_tokens["expires_at"] - timedelta(minutes=5)

class Email(Document):
    user_id: str
    platform: str
    email_id: str = Field(unique=True)
    categories: list[str]
    sender: str
    subject: str
    received_at: datetime
    is_processed: bool = False

    class Settings:
        name = "emails"
        indexes = [
            [("user_id", 1), ("received_at", -1)],
            [("categories", 1)]
        ]





