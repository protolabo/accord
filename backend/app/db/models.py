import uuid
from beanie import Document, PydanticObjectId
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Literal

# OAuth2 token model (access, refresh, expiration)
class TokenInfo(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None

    def is_expired(self) -> bool:
        if not self.expires_at:
            return True
        return datetime.now() > self.expires_at - timedelta(minutes=5)

# Linked email account model. Used to support multiple providers per user.
class EmailAccount(BaseModel):
    provider: Literal["outlook", "gmail"]
    email: EmailStr = Field(default=None, index=True)
    user_id_on_platform: str = Field(default=None, index=True)
    tokens: Optional[TokenInfo] = None
    display_name: Optional[str] = None
    profile_picture: Optional[str] = None
    primary: bool = False   # Indicates if this email account is the user's primary/default one

    @property
    def is_token_expired(self) -> bool:
        return self.tokens.is_expired() if self.tokens else True


class User(Document):
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True)
    accounts: List[EmailAccount] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "users"
        indexes = ["user_id", "accounts.email", "accounts.user_id_on_platform"]

    def preferred_account(self, valid_account: List[EmailAccount]) -> Optional[EmailAccount]:
        if not valid_account:
            return None
        for account in valid_account:
            if account.primary:
                return account
        return valid_account[0] # Fallback

    def get_valid_accounts(self, provider: Optional[str] = None) -> List[EmailAccount]:
        accounts = [acc for acc in self.accounts if acc.tokens and not acc.is_token_expired]
        if provider:
            accounts = [acc for acc in accounts if acc.provider == provider]
        return accounts
    
    # def get_account_for_email(self, email: Email) -> Optional[EmailAccount]:
    #     return next((acc for acc in self.accounts if acc.provider == email.platform and acc.user_id_on_platform == email.user_id), None)


class Email(Document):
    user_id: str
    platform: Literal["gmail", "outlook"]
    user_id_on_platform: str # For EmailAccount Search

    email_id: str = Field(index=True)
    thread_id: Optional[str] = None
    
    # Sender/recipient information
    sender: Optional[str] = None
    sender_email: EmailStr
    to: list[EmailStr]
    cc: Optional[list[EmailStr]] = Field(default_factory=list)
    bcc: Optional[list[EmailStr]] = Field(default_factory=list)
    
    # Content
    subject: str
    
    # Metadata
    received_at: datetime
    is_read: bool = False
    is_important: bool = False
    categories: list[str] = Field(default_factory=list)
    threads: list[str] = Field(default_factory=list)
    
    # Attachments
    attachments: Optional[List[dict]] = None
    
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


class EmailThread(Document):
    user_id: str
    name: str
    email_ids: List[PydanticObjectId] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "email_threads"
        indexes = [
            [("user_id", 1), ("name", 1)],
        ]


# class User(Document):
#     platform = None
#     # Microsoft/Outlook specific fields
#     microsoft_id: Optional[str] = Field(default=None, index=True)
#     outlook_tokens: Optional[dict] = Field(default=None)
#     microsoft_mail : Optional[str] = Field(default=None, index=True)
#     # Google/Gmail specific fields
#     google_id: Optional[str] = Field(default=None, index=True)
#     gmail_tokens: Optional[dict] = Field(default=None)
#     google_mail : Optional[str] = Field(default=None, index=True)
#     # Common fields
#     created_at: datetime = Field(default_factory=datetime.now)
#     display_name: Optional[str] = None
#     profile_picture: Optional[str] = None
#     preferred_email_service: Optional[str] = None  # 'gmail' or 'outlook'

#     class Settings:
#         name = "users"
#         indexes = [
#             "microsoft_mail",
#             "google_mail",
#             "microsoft_id",
#             "google_id"
#         ]

#     @property
#     def is_outlook_token_expired(self) -> bool:
#         if not self.outlook_tokens or not self.outlook_tokens.get("expires_at"):
#             return True
#         return datetime.now() > datetime.fromisoformat(str(self.outlook_tokens["expires_at"])) - timedelta(minutes=5)
    
#     @property
#     def is_gmail_token_expired(self) -> bool:
#         if not self.gmail_tokens or not self.gmail_tokens.get("expires_at"):
#             return True
#         return datetime.now() > datetime.fromisoformat(str(self.gmail_tokens["expires_at"])) - timedelta(minutes=5)
    
#     @property
#     def has_any_auth(self) -> bool:
#         return self.outlook_tokens is not None or self.gmail_tokens is not None
