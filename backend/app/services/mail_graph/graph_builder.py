from .nodes.user_node import UserNodeManager
from .nodes.message_node import MessageNodeManager
from .relations.user_relation import UserRelationManager
from .relations.message_relation import MessageRelationManager
from collections import defaultdict


class GraphBuilder:
    """Builds user and message graphs."""

    def __init__(self, central_user_email=None):
        """
        Initializes the graph builder.

        Args:
            central_user_email: Email of the central user (optional)
        """
        # Initialize node managers
        self.user_manager = UserNodeManager(central_user_email)
        self.message_manager = MessageNodeManager()

        # Initialize relation managers
        self.user_relation_manager = UserRelationManager()
        self.message_relation_manager = MessageRelationManager()

        # Main collections
        self.users = {}  # email -> user_node
        self.messages = {}  # message_id -> message_node
        self.user_relations = []  # list of all user relations
        self.message_relations = []  # list of all message relations

        self.central_user_email = central_user_email

    def process_email(self, email_data):
        """
        Processes an email and adds nodes and relations to the graphs.

        Args:
            email_data: Email data

        Returns:
            bool: True if the email was processed successfully, False otherwise
        """
        try:
            # Create message node
            message = self.message_manager.create_message(email_data, self.messages)
            if not message:
                return False

            # Process the email sender
            from_user = self.user_manager.get_or_create_user(email_data.get("From", ""), self.users)
            if not from_user:
                return False

            # Process the main recipients (To)
            to_emails = email_data.get("To", "").split(",") if email_data.get("To") else []
            for email in to_emails:
                if not email.strip():
                    continue

                to_user = self.user_manager.get_or_create_user(email.strip(), self.users)
                if to_user:
                    # Create EMAILED relation between users (initialize with 0)
                    emailed_rel = self.user_relation_manager.create_relation(from_user, to_user, "EMAILED", 0)
                    if emailed_rel not in self.user_relations:
                        self.user_relations.append(emailed_rel)

                    # Update connection strength
                    weight = 3 if from_user.get("is_central_user") else 1
                    self.user_relation_manager.update_connection_strength(from_user, to_user, weight=weight)

            # Process CC recipients
            cc_emails = email_data.get("Cc", "").split(",") if email_data.get("Cc") else []
            for email in cc_emails:
                if not email.strip():
                    continue

                cc_user = self.user_manager.get_or_create_user(email.strip(), self.users)
                if cc_user:
                    # Create EMAILED relation between users (initialize with 0)
                    emailed_cc_rel = self.user_relation_manager.create_relation(from_user, cc_user, "EMAILED", 0)
                    if emailed_cc_rel not in self.user_relations:
                        self.user_relations.append(emailed_cc_rel)

                    # Update connection strength with reduced weight for CC
                    weight = 1 if from_user.get("is_central_user") else 0.5
                    self.user_relation_manager.update_connection_strength(from_user, cc_user, weight=weight)

            # Process BCC recipients
            bcc_emails = email_data.get("Bcc", "").split(",") if email_data.get("Bcc") else []
            for email in bcc_emails:
                if not email.strip():
                    continue

                bcc_user = self.user_manager.get_or_create_user(email.strip(), self.users)
                if bcc_user:
                    # Create EMAILED relation between users (initialize with 0)
                    emailed_bcc_rel = self.user_relation_manager.create_relation(from_user, bcc_user, "EMAILED", 0)
                    if emailed_bcc_rel not in self.user_relations:
                        self.user_relations.append(emailed_bcc_rel)

                    # Update connection strength with even more reduced weight for BCC
                    weight = 0.9 if from_user.get("is_central_user") else 0.3
                    self.user_relation_manager.update_connection_strength(from_user, bcc_user, weight=weight)

            return True

        except Exception as e:
            print(f"Error processing email {email_data.get('Message-ID')}: {str(e)}")
            return False

    def build_message_thread_relations(self):
        """
        Builds relations between messages belonging to the same thread.
        """
        # Group messages by thread_id
        thread_messages = defaultdict(list)

        for message_id, message in self.messages.items():
            thread_id = message.get("thread_id")
            if thread_id:
                thread_messages[thread_id].append(message_id)

        # Process each thread
        for thread_id, message_ids in thread_messages.items():
            # Ignore threads with a single message
            if len(message_ids) <= 1:
                continue

            # Get the messages
            thread_msgs = [self.messages[mid] for mid in message_ids if mid in self.messages]

            # Sort messages by date
            sorted_messages = sorted(thread_msgs, key=lambda x: x.get("date", ""))

            # Create REPLIED_TO relations between consecutive messages
            for i in range(1, len(sorted_messages)):
                previous = sorted_messages[i - 1]
                current = sorted_messages[i]

                # Create REPLIED_TO relation
                replied_relation = self.message_relation_manager.create_thread_relation(
                    current, previous, "REPLIED_TO", 1.0
                )
                self.message_relations.append(replied_relation)