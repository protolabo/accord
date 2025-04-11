from datetime import datetime
from ..utils.email_utils import normalize_email


def _normalize_email(email):
    return normalize_email(email)


class MessageNodeManager:
    def __init__(self):
        """Initialise le gestionnaire de nœuds messages."""
        pass

    def create_message(self, email_data, messages_dict, central_user_email=None):
        """
        Creates a message node from the email data.
        Args:
        email_data: Email data
        messages_dict: Dictionary of existing messages
        central_user_email: Central user's email (optional)

        Returns:
        dict: Message node created
        """

        message_id = email_data.get("Message-ID")
        if not message_id:
            return None

        # Reply All have the same ID ?
        if message_id in messages_dict:
            return messages_dict[message_id]

        # Convert date to datetime format ( real date )
        date_str = email_data.get("Internal-Date")
        date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))

        # Normalize emails
        to_list = email_data.get("To", "").split(",") if email_data.get("To") else []
        cc_list = email_data.get("Cc", "").split(",") if email_data.get("Cc") else []
        bcc_list = email_data.get("Bcc", "").split(",") if email_data.get("Bcc") else []

        from_email = _normalize_email(email_data.get("From", ""))
        to_emails = [_normalize_email(e) for e in to_list if e.strip()]
        cc_emails = [_normalize_email(e) for e in cc_list if e.strip()]
        bcc_emails = [_normalize_email(e) for e in bcc_list if e.strip()]

        # Create a message node
        message = {
            "id": message_id,
            "type": "message",
            "thread_id": email_data.get("Thread-ID", ""),
            "date": date.isoformat(),
            "labels": email_data.get("Labels", []),
            "categories": email_data.get("Categories", []),
            "attachment": email_data.get("Attachments", []),
            "from": from_email,
            "to": to_emails,
            "cc": cc_emails,
            "bcc": bcc_emails,
        }

        messages_dict[message_id] = message

        return message