from datetime import datetime
from ..utils.email_utils import normalize_email


class MessageNodeManager:
    """Manager for message nodes in the graph."""

    def __init__(self):
        """Initializes the message node manager."""
        pass

    def create_message(self, email_data, messages_dict):
        """
        Creates a message node from email data.

        Args:
            email_data: Email data
            messages_dict: Dictionary of existing messages

        Returns:
            dict: Created message node
        """
        message_id = email_data.get("Message-ID")
        if not message_id:
            return None

        # If the message already exists, return it
        if message_id in messages_dict:
            return messages_dict[message_id]

        # Convert date to datetime format
        date_str = email_data.get("Internal-Date")
        if not date_str:
            date = datetime.now()
        else:
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))

        # Normalize emails
        to_list = email_data.get("To", "").split(",") if email_data.get("To") else []
        from_email = normalize_email(email_data.get("From", ""))
        to_emails = [normalize_email(e) for e in to_list if e.strip()]

        # Create a message node
        message = {
            "id": message_id,
            "type": "message",
            "thread_id": email_data.get("Thread-ID", ""),
            "date": date.isoformat(),
            "subject": email_data.get("Subject", ""),
            "from": from_email,
            "to": to_emails,
            "relations": []
        }

        messages_dict[message_id] = message
        return message