import os
import json
from .json_serializer import serialize_node, save_to_json


class GraphStorage:
    """Manages the storage of graphs in JSON files."""

    def __init__(self, output_dir):
        """
        Initializes the graph storage with separate directories for each graph.

        Args:
            output_dir: Main output directory
        """
        self.output_dir = output_dir

        # Create the main directory
        os.makedirs(output_dir, exist_ok=True)

        # Define and create subdirectories for each graph
        self.user_graph_dir = os.path.join(output_dir, "user_graph")
        self.message_graph_dir = os.path.join(output_dir, "message_graph")

        os.makedirs(self.user_graph_dir, exist_ok=True)
        os.makedirs(self.message_graph_dir, exist_ok=True)

    def save_user_graph(self, users, user_relations):
        """
        Saves the user graph in its dedicated directory.

        Args:
            users: Dictionary of user nodes
            user_relations: List of user relations
        """
        users_file = os.path.join(self.user_graph_dir, "users.json")
        save_to_json(users, users_file)

        relations_file = os.path.join(self.user_graph_dir, "relations.json")
        save_to_json(user_relations, relations_file)

    def save_message_graph(self, messages, message_relations):
        """
        Saves the message graph in its dedicated directory.

        Args:
            messages: Dictionary of message nodes
            message_relations: List of message relations
        """
        messages_file = os.path.join(self.message_graph_dir, "messages.json")
        save_to_json(messages, messages_file)

        relations_file = os.path.join(self.message_graph_dir, "relations.json")
        save_to_json(message_relations, relations_file)

    def save_metadata(self, metadata):
        """
        Saves the global project metadata in the main directory.

        Args:
            metadata: Metadata to save
        """
        # Update paths in metadata to reflect the new structure
        if "output_files" in metadata:
            metadata["output_files"] = {
                "user_graph": {
                    "users": os.path.join("user_graph", "users.json"),
                    "relations": os.path.join("user_graph", "relations.json")
                },
                "message_graph": {
                    "messages": os.path.join("message_graph", "messages.json"),
                    "relations": os.path.join("message_graph", "relations.json")
                }
            }

        metadata_file = os.path.join(self.output_dir, "metadata.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    def load_user_graph(self):
        """
        Loads the user graph from its dedicated directory.

        Returns:
            tuple: (users, relations)
        """
        users = self._load_json_file(os.path.join(self.user_graph_dir, "users.json"))
        relations = self._load_json_file(os.path.join(self.user_graph_dir, "relations.json"))
        return users, relations

    def load_message_graph(self):
        """
        Loads the message graph from its dedicated directory.

        Returns:
            tuple: (messages, relations)
        """
        messages = self._load_json_file(os.path.join(self.message_graph_dir, "messages.json"))
        relations = self._load_json_file(os.path.join(self.message_graph_dir, "relations.json"))
        return messages, relations

    def _load_json_file(self, filepath):
        """
        Loads a JSON file.

        Args:
            filepath: Complete file path

        Returns:
            Loaded data or None in case of error
        """
        if not os.path.exists(filepath):
            print(f"File {os.path.basename(filepath)} not found at {filepath}")
            return None

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {os.path.basename(filepath)}: {str(e)}")
            return None