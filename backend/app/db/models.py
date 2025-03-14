from beanie import Document, Indexed
from datetime import datetime
from typing import Optional

class User(Document):
    username: Indexed(str, unique=True)
    email: Indexed(str, unique=True)
    password_hash: str
    email_providers: list[dict] = []
    created_at: datetime = datetime.now()
    
    class Settings:
        name = "users"

class Email(Document):
    user_id: str
    platform: str
    raw_data: dict
    processed: Optional[dict] = None
    metadata: dict
    created_at: datetime = datetime.now()

    class Settings:
        name = "emails"
        indexes = [
            [("user_id", 1), ("metadata.date", -1)],  # 复合索引
            [("processed.priority", -1)]
        ]