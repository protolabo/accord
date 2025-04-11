import os
import json
from .word_indexer import WordIndexer
from .entity_indexer import EntityIndexer
from .subject_indexer import SubjectIndexer


class IndexManager:

    def __init__(self):
        self.word_indexer = WordIndexer()
        self.entity_indexer = EntityIndexer()
        self.subject_indexer = SubjectIndexer()

        self.word_index = self.word_indexer.get_index()
        self.entity_index = self.entity_indexer.get_index()
        self.subject_index = self.subject_indexer.get_index()

    def index_message(self, message_id, subject, body_text):
        """
        Indexes the contents of a message using specific indexers.

        Args:
        message_id: Message ID
        subject: Subject line
        body_text: Message body
        """
        if not message_id:
            return

        # Index subject
        self.subject_indexer.index_text(message_id, subject)

        words, entities = self.word_indexer.process_text(body_text)

        for word in words:
            self.word_indexer.add_to_index(word, message_id)

        for entity in entities:
            self.entity_indexer.add_to_index(entity, message_id)

    def save_indices(self, output_dir):
        """
        Backs up all indexes to files.

        Args:
        output_dir: Directory to save indexes to
        """
        indices_dir = os.path.join(output_dir, "indices")
        os.makedirs(indices_dir, exist_ok=True)

        # set to list
        def serialize_index(index):
            return {key: list(values) for key, values in index.items()}

        with open(os.path.join(indices_dir, "word_index.json"), 'w') as f:
            json.dump(serialize_index(self.word_index), f)

        with open(os.path.join(indices_dir, "entity_index.json"), 'w') as f:
            json.dump(serialize_index(self.entity_index), f)

        with open(os.path.join(indices_dir, "subject_index.json"), 'w') as f:
            json.dump(serialize_index(self.subject_index), f)

    def load_indices(self, indices_dir):
        """
        Load indexes from files.

        Args:
        indices_dir: Directory containing index files
        """
        if not os.path.exists(indices_dir):
            return

        # list to set
        def deserialize_index(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
                return {key: set(values) for key, values in data.items()}

        try:
            self.word_index = deserialize_index(os.path.join(indices_dir, "word_index.json"))
            self.entity_index = deserialize_index(os.path.join(indices_dir, "entity_index.json"))
            self.subject_index = deserialize_index(os.path.join(indices_dir, "subject_index.json"))


            self.word_indexer.set_index(self.word_index)
            self.entity_indexer.set_index(self.entity_index)
            self.subject_indexer.set_index(self.subject_index)


        except Exception as e:
            print(f"Error loading indexes: {str(e)}")