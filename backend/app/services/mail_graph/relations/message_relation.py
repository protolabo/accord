import uuid


class MessageRelationManager:
    """Manager for relations between messages."""

    def __init__(self):
        """Initializes the message relation manager."""
        pass

    def create_thread_relation(self, source_message, target_message, relation_type="REPLIED_TO", weight=1.0):
        """
        Creates a relation between two messages in the same thread.

        Args:
            source_message: Source message
            target_message: Target message
            relation_type: Relation type
            weight: Relation weight

        Returns:
            dict: Created relation
        """
        if not source_message or not target_message:
            return None

        # Create the relation
        relation = {
            "id": str(uuid.uuid4()),
            "type": "relation",
            "source_id": source_message["id"],
            "target_id": target_message["id"],
            "relation_type": relation_type,
            "weight": weight,
            "thread_id": source_message.get("thread_id", "")
        }

        # Add the relation to the source message's relations list
        source_message["relations"].append(relation)

        return relation