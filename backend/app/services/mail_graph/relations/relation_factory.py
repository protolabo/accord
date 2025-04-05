import uuid


class RelationFactory:
    """ create different types of relations in the email graph."""

    def __init__(self):
        pass

    def create_relation(self, source, target, relation_type, weight=1):
        """
        Creates a base relation between two nodes.

        Args:
            source: Source node
            target: Target node
            relation_type: Relation type
            weight: Relationship weight

        Returns:
            dict: Relationship object
        """

        if not source.get("id") or not target.get("id"):
            return None

        # Create the relation
        relation = {
            "id": str(uuid.uuid4()),
            "type": "relation",
            "source_id": source["id"],
            "target_id": target["id"],
            "relation_type": relation_type,
            "weight": weight,
        }

        return relation

    def create_sent_relation(self, user, message,weight):
        """
            Creates a SENT_relation between a user and a message.

        Args:
            user: User node (sender)
            message: Message node
            weight : Relation weight

        Returns:
            dict: SENT_relation
        """
        return self.create_relation(user, message, "SENT",weight)

    def create_received_relation(self, message, user):
        """
        Creates a RECEIVED relation between a message and a user.

        Args:
            message: Message node
            user: User node (recipient)

        Returns:
            dict: RECEIVED relation
        """
        return self.create_relation(message, user, "RECEIVED")

    def create_cc_relation(self, message, user):
        """
        Creates a CC relation between a message and a user.

        Args:
            message: Message node
            user: User node (in copy)

        Returns:
            dict: CC Relation
        """
        return self.create_relation(message, user, "CC")

    def create_bcc_relation(self, message, user):
        """
        Creates a BCC relation between a message and a user.

        Args:
            message: Message node
            user: User node (in hidden copy)

        Returns:
            dict: BCC Relation
        """
        return self.create_relation(message, user, "BCC")

    def create_emailed_relation(self, from_user, to_user):
        """
        Creates an EMAILED relation between two users.

        Args:
        from_user: Sender user node
        to_user: Recipient user node

        Returns:
        dict: EMAILED relation
        """
        return self.create_relation(from_user, to_user, "EMAILED")

    def create_emailed_cc_relation(self, from_user, cc_user):
        """
        Creates an EMAILED_CC relation between two users.

        Args:
        from_user: Sending user node
        cc_user: CC user node

        Returns:
        dict: EMAILED_CC relation
        """
        return self.create_relation(from_user, cc_user, "EMAILED_CC")

    def create_emailed_bcc_relation(self, from_user, cc_user):
        """
        Creates an EMAILED_BCC relation between two users.

        Args:
        from_user: Sending user node
        cc_user: BCC user node

        Returns:
        dict: EMAILED_CC relation
        """
        return self.create_relation(from_user, cc_user, "EMAILED_BCC_CC")



    def create_topic_relation(self, message, topic, weight=1):
        """
        Creates a HAS_TOPIC relationship between a message and a topic.

        Args:
        message: Message node
        topic: Topic node
        weight: Relationship weight

        Returns:
        dict: HAS_TOPIC relationship
        """
        relation = self.create_relation(message, topic, "HAS_TOPIC", weight=weight)


        return relation