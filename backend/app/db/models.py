from beanie import Document
from datetime import datetime, timedelta
from pydantic import Field, EmailStr
from pydantic import ConfigDict
from typing import Optional

class User(Document):
    email: EmailStr = Field(index=True)
    # Microsoft/Outlook specific fields
    microsoft_id: Optional[str] = Field(default=None, index=True)
    outlook_tokens: Optional[dict] = Field(default=None)
    # Google/Gmail specific fields
    google_id: Optional[str] = Field(default=None, index=True)
    gmail_tokens: Optional[dict] = Field(default=None)
    # Common fields
    created_at: datetime = Field(default_factory=datetime.now)
    display_name: Optional[str] = None
    profile_picture: Optional[str] = None
    preferred_email_service: Optional[str] = None  # 'gmail' or 'outlook'

    class Settings:
        name = "users"
        indexes = [
            "email",
            "microsoft_id",
            "google_id"
        ]

    @property
    def is_outlook_token_expired(self) -> bool:
        if not self.outlook_tokens or not self.outlook_tokens.get("expires_at"):
            return True
        return datetime.now() > datetime.fromisoformat(str(self.outlook_tokens["expires_at"])) - timedelta(minutes=5)
    
    @property
    def is_gmail_token_expired(self) -> bool:
        if not self.gmail_tokens or not self.gmail_tokens.get("expires_at"):
            return True
        return datetime.now() > datetime.fromisoformat(str(self.gmail_tokens["expires_at"])) - timedelta(minutes=5)
    
    @property
    def has_any_auth(self) -> bool:
        return self.outlook_tokens is not None or self.gmail_tokens is not None

class Email(Document):
    user_id: str
    platform: str  # 'gmail' or 'outlook'
    email_id: str = Field(index=True)
    external_id: str = Field(index=True)  # ID from Gmail or Outlook
    thread_id: Optional[str] = None
    
    # Sender/recipient information
    sender: str
    sender_email: EmailStr
    to: list[str]
    cc: list[str] = Field(default_factory=list)
    bcc: list[str] = Field(default_factory=list)
    
    # Content
    subject: str
    body: str
    body_type: str = "text"  # 'text' or 'html'
    
    # Metadata
    received_at: datetime
    is_read: bool = False
    is_important: bool = False
    categories: list[str] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)
    
    # Attachments
    has_attachments: bool = False
    attachments: list[dict] = Field(default_factory=list)
    
    # Processing status
    is_processed: bool = False
    processing_metadata: Optional[dict] = None

    class Settings:
        name = "emails"
        indexes = [
            [("user_id", 1), ("received_at", -1)],
            [("platform", 1)],
            [("categories", 1)],
            [("external_id", 1)]
        ]

    def standardize(self) -> dict:
        """
        Standardizes the email format for frontend consumption
        """
        return {
            "id": str(self.id),
            "external_id": self.external_id,
            "subject": self.subject,
            "from": self.sender,
            "from_email": self.sender_email,
            "to": self.to,
            "cc": self.cc,
            "body": self.body,
            "bodyType": self.body_type,
            "date": self.received_at.isoformat(),
            "isRead": self.is_read,
            "isImportant": self.is_important,
            "attachments": self.attachments,
            "categories": self.categories,
            "labels": self.labels,
            "platform": self.platform,
            "threadId": self.thread_id
        }





