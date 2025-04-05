import uuid
from ..utils.email_utils import normalize_email,extract_email_parts

def _normalize_email(email):
    return normalize_email(email)

class UserNodeManager:
    """Manager for user nodes in the graph."""

    def __init__(self, central_user_email=None):
        self.central_user_email = _normalize_email(central_user_email) if central_user_email else None


    def get_or_create_user(self, email_address, users_dict):
        """
        Gets or creates a user node

        Args:
            email_address: User's email address
            users_dict: Dictionary of existing users

        Returns:
            dict: User node
        """
        if not email_address:
            return None

        clean_email = _normalize_email(email_address)

        if clean_email in users_dict:
            return users_dict[clean_email]

        # Extract parts of the email
        email, domain, name = extract_email_parts(email_address)

        # Create a new user
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "type": "user",
            "email": clean_email,
            "name": name,
            "domain": domain,
            "is_central_user": clean_email == self.central_user_email,
            "connection_strength": 0
        }

        users_dict[clean_email] = user

        return user