import uuid


class UserRelationManager:
    """Manager for relations between users."""

    def __init__(self):
        """Initializes the user relation manager."""
        pass

    def create_relation(self, from_user, to_user, relation_type="EMAILED", weight=1.0):
        """
        Creates a relation between two users or updates its weight if it already exists.

        Args:
            from_user: Source user
            to_user: Destination user
            relation_type: Relation type
            weight: Initial weight of the relation

        Returns:
            dict: Created or updated relation
        """
        if not from_user or not to_user:
            return None

        # Check if the relation already exists
        existing_relation = None
        for rel in from_user.get("relations", []):
            if (rel.get("relation_type") == relation_type and
                    rel.get("target_id") == to_user["id"]):
                existing_relation = rel
                break

        if existing_relation:
            # Don't overwrite the existing weight if we're initializing with zero
            if weight > 0:
                existing_relation["weight"] = weight
            return existing_relation

        # Create a new relation
        relation = {
            "id": str(uuid.uuid4()),
            "type": "relation",
            "source_id": from_user["id"],
            "target_id": to_user["id"],
            "relation_type": relation_type,
            "weight": weight,
            "from_user": from_user["email"],
            "to_user": to_user["email"]
        }

        # Add the relation to the source user's relations list
        if "relations" not in from_user:
            from_user["relations"] = []
        from_user["relations"].append(relation)

        return relation

    def update_connection_strength(self, from_user, to_user, weight=1.0):
        """
        Updates the connection strength between two users.

        Args:
            from_user: First user
            to_user: Second user
            weight: Weight to add to the connection
        """
        if not from_user or not to_user:
            return

        # Update the connection strength in the user
        to_user["connection_strength"] = to_user.get("connection_strength", 0) + weight

        # Also update the relation weight
        for rel in from_user.get("relations", []):
            if rel.get("target_id") == to_user["id"] and rel.get("relation_type") == "EMAILED":
                rel["weight"] = rel.get("weight", 0) + weight
                break