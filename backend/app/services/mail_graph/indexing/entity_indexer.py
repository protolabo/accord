from collections import defaultdict

class EntityIndexer:

    def __init__(self):
        # Inverted index structure: entity -> set of message IDs
        self.index = defaultdict(set)

        self.processed_messages = set()

        try:
            import spacy
            self.nlp = spacy.load("fr_core_news_sm")
            self.has_nlp = True
        except (ImportError, OSError):
            self.nlp = None
            self.has_nlp = False

    def extract_entities(self, text):
        """
        Extracts named entities from a text.

        Args:
        text: Text to analyze

        Returns:
        list: List of extracted entities
        """
        if not text:
            return []

        entities = []

        if self.has_nlp:
            # Use spaCy to extract entities
            doc = self.nlp(text)
            for ent in doc.ents:
                if len(ent.text) > 2:
                    entities.append(ent.text.lower())
        else:
            return None

        return entities

    def add_to_index(self, entity, message_id):
        """
        Adds an entity to the index for a specific message.

        Args:
        entity: Entity to index
        message_id: ID of the message containing this entity
        """
        if not entity or not message_id:
            return

        entity = entity.lower().strip()

        if len(entity) < 3:
            return

        self.index[entity].add(message_id)

    def index_message(self, message_id, text):
        """
        Indexes all entities in a message.

        Args:
        message_id: Message ID
        text: Message text
        """
        if not message_id or message_id in self.processed_messages:
            return

        self.processed_messages.add(message_id)

        entities = self.extract_entities(text)

        # add entity to index
        for entity in entities:
            self.add_to_index(entity, message_id)



    def get_index(self):
        return self.index

    def set_index(self, index):
        self.index = defaultdict(set)

        for entity, message_ids in index.items():
            self.index[entity] = set(message_ids)