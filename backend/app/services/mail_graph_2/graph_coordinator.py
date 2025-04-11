import gc
from datetime import datetime
from .graph_builder import GraphBuilder
from .utils.graph_storage import GraphStorage


class GraphCoordinator:
    """Coordinates the complete process of building graphs."""

    def __init__(self, central_user_email=None, output_dir="./output/graph"):
        """
        Initializes the graph coordinator.

        Args:
            central_user_email: Email of the central user (optional)
            output_dir: Output directory
        """
        self.central_user_email = central_user_email
        self.output_dir = output_dir

        # Main components
        self.graph_builder = GraphBuilder(central_user_email)
        self.graph_storage = GraphStorage(output_dir)

    def build_graphs(self, emails):
        """
        Builds user and message graphs.

        Args:
            emails: List of emails to process

        Returns:
            dict: Metadata of the constructed graphs
        """
        print(f"Building graphs for {len(emails)} emails...")

        # Phase 1: Building basic structures
        print("Phase 1: Building basic graph structures...")

        batch_size = 5000
        processed_count = 0

        for i in range(0, len(emails), batch_size):
            end = min(i + batch_size, len(emails))
            print(f"Processing emails {i}-{end}...")

            batch_processed = 0
            for email in emails[i:end]:
                # Email processing step
                if self.graph_builder.process_email(email):
                    batch_processed += 1
                    processed_count += 1

            print(f"Batch completed: {batch_processed} processed")

            # Free memory
            gc.collect()

        # Phase 2: Building thread relations between messages
        print("Phase 2: Building thread relations between messages...")
        self.graph_builder.build_message_thread_relations()

        # Save graphs
        print("Saving graphs...")
        self.graph_storage.save_user_graph(
            self.graph_builder.users,
            self.graph_builder.user_relations
        )

        self.graph_storage.save_message_graph(
            self.graph_builder.messages,
            self.graph_builder.message_relations
        )

        # Create metadata
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "total_emails_processed": processed_count,
            "users_count": len(self.graph_builder.users),
            "messages_count": len(self.graph_builder.messages),
            "user_relations_count": len(self.graph_builder.user_relations),
            "message_relations_count": len(self.graph_builder.message_relations),
            "central_user_email": self.central_user_email,
            "output_files": {
                "users": "users.json",
                "user_relations": "user_relations.json",
                "messages": "messages.json",
                "message_relations": "message_relations.json"
            }
        }

        self.graph_storage.save_metadata(metadata)

        return metadata