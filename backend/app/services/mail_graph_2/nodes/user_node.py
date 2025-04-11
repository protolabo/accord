import uuid
from ..utils.email_utils import normalize_email, extract_email_parts


class UserNodeManager:
    """Manager for user nodes in the graph."""

    def __init__(self, central_user_email=None):
        """
        Initializes the user node manager.

        Args:
            central_user_email: Email of the central user (optional)
        """
        self.central_user_email = normalize_email(central_user_email) if central_user_email else None

    def get_or_create_user(self, email_address, users_dict):
        """
        Retrieves or creates a user node.

        Args:
            email_address: User's email address
            users_dict: Dictionary of existing users

        Returns:
            dict: User node
        """
        if not email_address:
            return None

        clean_email = normalize_email(email_address)
        if not clean_email:
            return None

        if clean_email in users_dict:
            return users_dict[clean_email]

        # Extract parts of the email
        email, domain, name = extract_email_parts(clean_email)

        # Create a new user
        user = {
            "id": str(uuid.uuid4()),
            "type": "user",
            "email": clean_email,
            "name": name,
            "domain": domain,
            "is_central_user": clean_email == self.central_user_email,
            "connection_strength": 0,
            "relations": []
        }

        users_dict[clean_email] = user
        return user