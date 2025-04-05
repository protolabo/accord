from ..utils.email_utils import normalize_email


def _normalize_email(email):
    return normalize_email(email)

class ConnectionStrengthManager:

    def __init__(self, central_user_email=None):
        self.central_user_email = central_user_email

    def update_connection_strength(self, user1, user2, weight=1):
        """
        Updates the connection strength between two users.

        Args:
        user1: First user node
        user2: Second user node
        weight: Connection weight
        """
        # Update  strength if one of the users is main user
        if not self.central_user_email:
            return

        central_email = _normalize_email(self.central_user_email)

        email1 = user1.get("email", "")
        email2 = user2.get("email", "")

        # Update connexion strength for user who is not the central user
        if email1 == central_email:

            # Also update the force in the user node
            if "connection_strength" in user2:
                user2["connection_strength"] = user2.get("connection_strength", 0) + weight

        elif email2 == central_email:

            # Also update the force in the user node
            if "connection_strength" in user1:
                user1["connection_strength"] = user1.get("connection_strength", 0) + weight

