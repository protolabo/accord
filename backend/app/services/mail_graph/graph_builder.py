from .nodes.user_node import UserNodeManager
from .nodes.message_node import MessageNodeManager
from .nodes.thread_node import ThreadNodeManager
from .nodes.topic_node import TopicNodeManager
from .relations.relation_factory import RelationFactory
from .relations.connection_strength import ConnectionStrengthManager


class GraphBuilder:

    def __init__(self, central_user_email=None):

        # Initialize node managers
        self.user_manager = UserNodeManager(central_user_email)
        self.message_manager = MessageNodeManager()
        self.thread_manager = ThreadNodeManager()
        self.topic_manager = TopicNodeManager()

        # Initialize the relationship manager
        self.relation_factory = RelationFactory()

        # Connection strength manager
        self.connection_manager = ConnectionStrengthManager(central_user_email)

        # Main collections
        self.users = {}  # email -> user_node
        self.messages = {}  # message_id -> message_node
        self.threads = {}  # thread_id -> thread_node
        self.topics = {}  # topic_id -> topic_node
        self.relations = []  # list of all relations/edges

        # Reference to the central user
        self.central_user_email = central_user_email
        self.central_user_node = None

    def process_email(self, email_data):
        """
        Processes an email and adds the nodes and relationships to the graph.

        Returns:
        bool: True if the email was successfully processed, False otherwise.
        """
        try:
            # Create  message node
            message = self.message_manager.create_message(email_data, self.messages, self.central_user_email)
            if not message:
                return False

            # Update or create a thread for this message
            thread = self.thread_manager.get_or_create_thread(email_data, self.threads, self.central_user_email)

            #######
            # Treat the sender of the email
            from_user = self.user_manager.get_or_create_user(email_data.get("From", ""), self.users)

            # Creating the SENT_relation
            # link a sender to their message
            weight = 3 if from_user.get("is_central_user") else 1
            sent_relation = self.relation_factory.create_sent_relation(from_user, message, weight=weight)
            self.relations.append(sent_relation)


            #######
            # Process recipients (To)
            to_emails = email_data.get("To", "").split(",") if email_data.get("To") else []
            for email in to_emails:
                if not email.strip():
                    continue

                to_user = self.user_manager.get_or_create_user(email.strip(), self.users)
                if to_user:
                    # Create the RECEIVED relation
                    received_rel = self.relation_factory.create_received_relation(message, to_user)
                    self.relations.append(received_rel)

                    # Create the EMAILED relation between users
                    if from_user:
                        emailed_rel = self.relation_factory.create_emailed_relation(from_user, to_user)
                        self.relations.append(emailed_rel)

                        # Update connection strength
                        self.connection_manager.update_connection_strength(from_user, to_user)

            #####
            # Treat recipients as copied (CC)
            cc_emails = email_data.get("Cc", "").split(",") if email_data.get("Cc") else []
            for email in cc_emails:
                if not email.strip():
                    continue

                cc_user = self.user_manager.get_or_create_user(email.strip(), self.users)
                if cc_user:

                    # Create CC relation (Message→User)
                    cc_rel = self.relation_factory.create_cc_relation(message, cc_user)
                    self.relations.append(cc_rel)

                    # relation EMAILED_CC between Users
                    if from_user:
                        emailed_cc_rel = self.relation_factory.create_emailed_cc_relation(from_user, cc_user)
                        self.relations.append(emailed_cc_rel)

                        # Update connection strength (less weight for CC)
                        self.connection_manager.update_connection_strength(from_user, cc_user, weight=0.5)

            ######
            # Treat (BCC) recipients
            bcc_emails = email_data.get("Bcc", "").split(",") if email_data.get("Bcc") else []
            for email in bcc_emails:
                if not email.strip():
                    continue

                # create user node
                bcc_user = self.user_manager.get_or_create_user(email.strip(), self.users)
                if bcc_user:
                    # Create BCC relation (Message→User)
                    bcc_rel = self.relation_factory.create_bcc_relation(message, bcc_user)
                    self.relations.append(bcc_rel)

                    if from_user:
                        emailed_bcc_rel = self.relation_factory.create_emailed_bcc_relation(from_user, bcc_user)
                        self.relations.append(emailed_bcc_rel)

                        # Update connection strength (less weight for CC)
                        self.connection_manager.update_connection_strength(from_user, bcc_user, weight=0.3)


            ###############
            # Extract topics via the topic manager
            topics = self.topic_manager.extract_topics(email_data, self.topics)
            for topic in topics:
                topic_rel = self.relation_factory.create_topic_relation(message, topic)
                self.relations.append(topic_rel)

                # Add the topic to the thread's list of topics
                self.thread_manager.add_topic_to_thread(thread, topic)

            return True

        except Exception as e:
            print(f"Error processing email {email_data.get('Message-ID')}: {str(e)}")
            return False