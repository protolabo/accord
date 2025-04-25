import asyncio
from collections import defaultdict
from datetime import datetime
from beanie import PydanticObjectId
from typing import List, Dict

from backend.app.db.models import Email, EmailThread


# Generate thread for all user mails
async def generate_and_assign_threads(user_id: str) -> None:
    # 1. Get all emails of user in database
    emails = await Email.find(Email.user_id == user_id).to_list()

    # 2. Regroup by categories
    groups: defaultdict[str, list[PydanticObjectId]] = defaultdict(list)
    for mail in emails:
        # Put email in all threads while belongs to more than one categories
        for cat in mail.categories or []:
            groups[cat].append(mail.id)

    # 3. Generate threads for every categories
    for cat, ids in groups.items():
        now = datetime.now()
        thread = await EmailThread.find_one(
            (EmailThread.user_id == user_id) & (EmailThread.name == cat)
        )
        if thread:
            thread.email_ids = ids
            thread.updated_at = now
            await thread.save()
        else:
            thread = EmailThread(
                user_id=user_id,
                name=cat,
                email_ids=ids,
                created_at=now,
                updated_at=now,
            )
            await thread.insert()


# Generate thread for single new mails
async def assign_email_to_threads(email: Email) -> None:
    user_id = email.user_id
    email_id = email.id
    categories = email.categories or []
    if not categories:
        return

    now = datetime.now()
    for cat in categories:
        thread = await EmailThread.find_one(
            (EmailThread.user_id == user_id) & (EmailThread.name == cat)
        )
        if thread:
            if email_id not in thread.email_ids:
                thread.email_ids.append(email_id)
                thread.updated_at = now
                await thread.save()
        else:
            new_thread = EmailThread(
                user_id=user_id,
                name=cat,
                email_ids=[email_id],
                created_at=now,
                updated_at=now,
            )
            await new_thread.insert()

# Get all thread with corresponding email
async def get_all_threads_with_emails(user_id: str) -> List[Dict]:
    threads = await EmailThread.find(EmailThread.user_id == user_id).to_list()

    overview = []
    for thr in threads:
        # Handle thread with no mails
        if not thr.email_ids:
            overview.append({"threadName": thr.name, "emails": []})
            continue
        
        # Get email id and its subject
        mails = await Email.find(
            Email.id.in_(thr.email_ids)
        ).project(
            Email.id, Email.subject
        ).to_list()

        # Dict returned 
        overview.append({
            "threadName": thr.name,
            "emails": [
                {"id": str(m.id), "subject": m.subject}
                for m in mails
            ]
        })
    
    return overview