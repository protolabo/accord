from datetime import datetime
from ..utils.email_utils import normalize_email


def _normalize_email(email):
    return normalize_email(email)


class ThreadNodeManager:

    def __init__(self):
        pass

    def get_or_create_thread(self, email_data, threads_dict, central_user_email=None):
        """
        Gets or creates a conversation node (thread).

        Note : transforms emails_providers threads into nodes compatible with Accord data model.

        Args:
            email_data: Email data
            threads_dict: Dictionary of existing threads
            central_user_email: Central user's email (optional)
        Returns:
            dict: Threads Node created
        """

        thread_id = email_data.get("Thread-ID", "")
        if not thread_id:
            return None

        # Check if thread already exists
        if thread_id in threads_dict:
            thread = threads_dict[thread_id]

            # Update participants
            self._update_thread_participants(thread, email_data)

            # Update participants
            thread["message_count"] = thread.get("message_count", 0) + 1

            # Update the date of the last message ( => for sorting)
            date = datetime.fromisoformat(email_data["Internal-Date"].replace('Z', '+00:00'))
            thread["last_message_date"] = max(thread.get("last_message_date", ""), date.isoformat())

            return thread

        # Create a new thread
        thread = {
            "id": thread_id,
            "type": "thread",
            "participants": [],
            "first_message_id": email_data.get("Message-ID", ""),
            "message_count": 1,
            "last_message_date": "",
            "topics": []
            # "subject": email_data.get("Subject", ""),
        }

        # Add participants
        self._update_thread_participants(thread, email_data)

        # Set the date of the last message
        date = datetime.fromisoformat(email_data["Internal-Date"].replace('Z', '+00:00'))
        thread["last_message_date"] = date.isoformat()

        threads_dict[thread_id] = thread
        return thread

    def _update_thread_participants(self, thread, email_data):
        """
        Updates the list of participants in a thread.

        Args:
            thread: Thread node to update
            email_data: Email data
        """
        # Create a set of current participants
        participants = set(thread.get("participants", []))

        # Add sender
        from_email = email_data.get("From", "")
        if from_email:
            participants.add(from_email)

        # Add recipients
        to_emails = email_data.get("To", "").split(",") if email_data.get("To") else []
        cc_emails = email_data.get("Cc", "").split(",") if email_data.get("Cc") else []

        for email in to_emails + cc_emails:
            if email and email.strip():
                participants.add(email.strip())

        thread["participants"] = list(participants)


    def add_topic_to_thread(self, thread, topic):
        """
        Adds a topic to a thread if it isn't already present.

        Args:
            thread: Thread node
            topic: Subject node
        """
        if not thread or not topic:
            return

        # Add the topic if it is not already in the list
        topic_name = topic["name"]
        if topic_name not in thread["topics"]:
            thread["topics"].append(topic_name)