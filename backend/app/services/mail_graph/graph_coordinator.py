import gc
from datetime import datetime
from .graph_builder import GraphBuilder
from .relations.thread_processor import ThreadRelationProcessor
from .indexing.index_manager import IndexManager
from .utils.graph_storage import GraphStorage


class GraphCoordinator:
    """Coordinates the entire email graph building process."""

    def __init__(self, central_user_email=None, output_dir="./output/graph"):

        self.central_user_email = central_user_email
        self.output_dir = output_dir


        # Main Components
        self.graph_builder = GraphBuilder(central_user_email)

        #Handles relation between messages in the same thread
        self.thread_processor = ThreadRelationProcessor()

        #indexing messages for search
        self.index_manager = IndexManager()
        self.graph_storage = GraphStorage(output_dir)

    def build_graph_exec(self, emails):
        """
        Args:
        emails: List of emails to process
        Returns:
        dict: Metadata of the constructed graph
        """

        print(f"Building the graph for {len(emails)} emails ...")

        # Phase 1: Building the basic structure
        print("Phase 1: Building the basic graph structure...")

        # lots
        batch_size = 5000
        processed_count = 0

        ######################################################

        for i in range(0, len(emails), batch_size):
            end = min(i + batch_size, len(emails))
            print(f"Traitement des emails {i}-{end}...")

            batch_processed = 0
            for email in emails[i:end]:

                # mail processing step
                if self.graph_builder.process_email(email):
                    batch_processed += 1
                    processed_count += 1

                    # Indexing mail
                    self.index_manager.index_message(
                        email.get("Message-ID"),
                        email.get("Subject", ""),
                        email.get("Body", {}).get("plain", "")
                    )

            print(f"Batch completed: {batch_processed} processed")

            # free memory
            gc.collect()

        ###################################################

        # Save the basic structure
        print("Saving the basic graph structure...")
        self.graph_storage.save_nodes(
            self.graph_builder.users,
            self.graph_builder.messages,
            self.graph_builder.threads,
            self.graph_builder.topics
        )

        # Sauvegarder les index de recherche
        print("Saving search indexes...")
        self.index_manager.save_indices(self.output_dir)

        print("Phase 1: Completed. Basic structure saved.")

        # Phase 2: Processing Thread Relation
        print("Phase 2: Processing Thread Relations...")
        thread_relations = self.thread_processor.process_thread_relations(
            self.graph_builder.messages,
            self.graph_builder.threads
        )

        # union
        self.graph_builder.relations.extend(thread_relations)

        # Save thread relations
        thread_relations_count = len(thread_relations)
        self.graph_storage.save_thread_relations(thread_relations)

        gc.collect()

        # Phase 3:  get accord thread
        print("Phase 3: TODO,  get accord thread")


        metadata = {
            "timestamp": datetime.now().isoformat(),
            "total_emails_processed": processed_count,
            "users_count": len(self.graph_builder.users),
            "messages_count": len(self.graph_builder.messages),
            "threads_count": len(self.graph_builder.threads),
            "topics_count": len(self.graph_builder.topics),
            "thread_relations_count": thread_relations_count,
            "central_user_email": self.central_user_email,
            "output_files": {
                "users": "users.json",
                "messages": "messages.json",
                "threads": "threads.json",
                "topics": "topics.json",
                "thread_relations": "thread_relations.json",
                "similarity_relations": "similarity_relations.json"
            }
        }

        self.graph_storage.save_metadata(metadata)

        return metadata