import json
import random
from pathlib import Path
from typing import Optional, Set


class EnronDataManager:
    """
    Enron data management class for generating realistic emails
    with duplicate prevention and short message filtering
    """

    def __init__(self, enron_json_path: str, min_body_length: int = 100):
        """
        Initialize the Enron data manager

        Args:
            enron_json_path: Path to the JSON file containing Enron emails
            min_body_length: Minimum length of message bodies (in characters)
        """
        self.enron_json_path = enron_json_path
        self.min_body_length = min_body_length
        self.emails = []
        self.used_body_indices = set()
        self.used_subject_indices = set()
        # Keep track of already used message IDs to avoid duplicates
        self.used_message_ids: Set[str] = set()
        self._load_enron_data()

    def _load_enron_data(self) -> None:
        """
        Load Enron data from the JSON file
        """
        try:
            json_path = Path(self.enron_json_path)
            if not json_path.exists():
                print(f"Enron data file not found: {self.enron_json_path}")
                return

            with open(json_path, 'r', encoding='utf-8') as f:
                self.emails = json.load(f)

            print(f"Enron data successfully loaded: {len(self.emails)} emails")

            # Filter empty or too short emails at loading
            self.emails = [email for email in self.emails
                           if isinstance(email, dict)
                           and "body" in email
                           and email["body"]
                           and len(email["body"]) >= self.min_body_length]

            print(f"After filtering: {len(self.emails)} usable emails")

        except Exception as e:
            print(f"Error loading Enron data: {str(e)}")
            self.emails = []

    def is_data_available(self) -> bool:
        """
        Check if Enron data is available

        Returns:
            bool: True if data is available, False otherwise
        """
        return len(self.emails) > 0

    def get_email_count(self) -> int:
        """
        Return the number of available emails

        Returns:
            int: Number of loaded Enron emails
        """
        return len(self.emails)

    def get_random_email_body(self, max_attempts: int = 100) -> Optional[str]:
        """
        Return the body of a random email, long enough and unused

        Args:
            max_attempts: Maximum number of attempts to find an appropriate message

        Returns:
            str: Email body or None if no appropriate email is available
        """
        if not self.emails:
            return None

        # Reset tracking if all emails have already been used
        if len(self.used_message_ids) >= len(self.emails):
            print("All messages have been used, resetting tracking")
            self.used_message_ids.clear()

        last_body = None
        for attempt in range(max_attempts):
            # Select a random email
            index = random.randint(0, len(self.emails) - 1)
            email = self.emails[index]

            # Check if this message has already been used
            message_id = email.get("metadata", {}).get("message_id", str(index))

            if message_id in self.used_message_ids:
                continue  # Message already used, try another

            body = email.get("body", "")

            # Save this body as the last body found
            last_body = body

            # Check minimum length
            if len(body) >= self.min_body_length:
                # Mark this message as used
                self.used_message_ids.add(message_id)
                return body

        # If we get here, we've made max_attempts without success
        # Return the last body found, even if it doesn't meet the criteria
        print(f"After {max_attempts} attempts, no appropriate message was found")
        if last_body:
            return last_body

        # As a last resort, take any message
        random_index = random.randint(0, len(self.emails) - 1)
        return self.emails[random_index].get("body", "")

    def get_random_email_subject(self) -> Optional[str]:
        """
        Return the subject of a random email

        Returns:
            str: Email subject or None if none is available
        """
        if not self.emails:
            return None

        # If all subjects have already been used, reset
        if len(self.used_subject_indices) >= len(self.emails):
            self.used_subject_indices.clear()

        # Select an unused email for the subject
        available_indices = [i for i in range(len(self.emails)) if i not in self.used_subject_indices]
        if not available_indices:
            return None

        index = random.choice(available_indices)
        self.used_subject_indices.add(index)

        email = self.emails[index]

        # Extract subject from metadata
        metadata = email.get("metadata", {})
        subject = metadata.get("subject", "")

        # If the subject is empty or too short, try another
        if not subject or len(subject) < 5:
            return self.get_random_email_subject()

        # Clean the subject (remove RE:, FWD:, etc. and excess spaces)
        subject = self._clean_subject(subject)

        return subject

    def _clean_subject(self, subject: str) -> str:
        """
        Clean an email subject

        Args:
            subject: Original subject

        Returns:
            str: Cleaned subject
        """
        if not subject:
            return ""

        # Remove reply and forward prefixes
        prefixes = ["RE:", "FW:", "FWD:", "Re:", "Fw:", "Fwd:"]

        cleaned_subject = subject
        for prefix in prefixes:
            while cleaned_subject.startswith(prefix):
                cleaned_subject = cleaned_subject[len(prefix):].strip()

        # Remove excess spaces
        cleaned_subject = cleaned_subject.strip()

        return cleaned_subject