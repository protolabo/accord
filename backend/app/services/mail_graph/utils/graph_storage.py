import os
import json
from .json_serializer import serialize_node


class GraphStorage:


    def __init__(self, output_dir):

        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def save_nodes(self, users, messages, threads, topics):
        """
        Saves all nodes in the graph.

        Args:
        users: Dictionary of user nodes
        messages: Dictionary of message nodes
        threads: Dictionary of thread nodes
        topics: Dictionary of topic nodes
        """

        users_file = os.path.join(self.output_dir, "users.json")
        self._save_dict_to_json(users, users_file)

        messages_file = os.path.join(self.output_dir, "messages.json")
        self._save_dict_to_json(messages, messages_file)


        threads_file = os.path.join(self.output_dir, "threads.json")
        self._save_dict_to_json(threads, threads_file)


        topics_file = os.path.join(self.output_dir, "topics.json")
        self._save_dict_to_json(topics, topics_file)

    def save_thread_relations(self, relations):

        relations_file = os.path.join(self.output_dir, "thread_relations.json")
        self._save_list_to_json(relations, relations_file)



    def save_metadata(self, metadata):
        metadata_file = os.path.join(self.output_dir, "metadata.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    def _save_dict_to_json(self, data_dict, filepath):

        serialized_data = {k: serialize_node(v) for k, v in data_dict.items()}
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(serialized_data, f, ensure_ascii=False)

    def _save_list_to_json(self, data_list, filepath):

        serialized_data = [serialize_node(item) for item in data_list]
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(serialized_data, f, ensure_ascii=False)

    def load_graph(self):
        graph = {
            "users": self._load_json_file("users.json"),
            "messages": self._load_json_file("messages.json"),
            "threads": self._load_json_file("threads.json"),
            "topics": self._load_json_file("topics.json"),
            "relations": []
        }

        thread_relations = self._load_json_file("thread_relations.json")
        if thread_relations:
            graph["relations"].extend(thread_relations)



    def _load_json_file(self, filename):
        filepath = os.path.join(self.output_dir, filename)
        if not os.path.exists(filepath):
            print(f"Fichier {filename} non trouvé.")
            return None

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erreur lors du chargement de {filename}: {str(e)}")
            return None