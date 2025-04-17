from datetime import datetime
from app.services.email.email_provider import EmailProvider
from app.db.models import Email
from app.services.ai.pipeline import process_email

# Classify and save single email
async def handle_single_email(
    raw: dict,
    user_id: str,
    platform: str,
    user_id_on_platform: str
):
    processed = process_email(raw)
    update_data = {
        "user_id": user_id,
        "platform": platform,
        "user_id_on_platform": user_id_on_platform,
        "subject":    processed["subject"],
        "body":       processed["sanitized_body"],
        "categories": processed["main_class"],
        "labels":     processed["sub_classes"],
        "is_processed": True,
        "processing_metadata": {
            "recognized_date": processed["recognized_date"],
        }
    }
    await Email.find_one(Email.external_id == processed["external_id"]).upsert({"$set": update_data})


async def sync_emails_for_user(user, since: datetime) -> dict:
    provider = EmailProvider(user)
    raw_emails = await provider.get_emails(since=since)
    for raw in raw_emails:
        await handle_single_email(
            raw=raw,
            user_id=str(user.id),
            platform=raw["platform"],
            user_id_on_platform=user.accounts[0].user_id_on_platform
        )
    return {"synced_count": len(raw_emails)}