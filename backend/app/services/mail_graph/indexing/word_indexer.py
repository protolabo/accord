from collections import defaultdict
from ..nlp.text_processor import process_text_with_spacy, fallback_text_processing
from ..stopword import stopwords as mystopwords


class WordIndexer:
    """Indexer for words contained in the body of messages."""

    def __init__(self):
        # Inverted index structure: word -> set of message IDs
        self.index = defaultdict(set)

        self.processed_messages = set()

        self.stop_words = mystopwords()

        try:
            import spacy
            self.nlp = spacy.load("fr_core_news_sm")
        except (ImportError, OSError):
            self.nlp = None


    def process_text(self, text):
        """
        Processes a text to extract words and entities.

        Args:
        text: Text to process

        Returns:
        tuple: List of words, list of entities
        """
        if self.nlp:
            return process_text_with_spacy(text, False, self.nlp, self.stop_words)
        else:
            # Fallback  if spaCy mot available
            return fallback_text_processing(text, self.stop_words), []

    def add_to_index(self, word, message_id):
        """
        Adds a word to the index for a specific message.

        Args:
        word: Word to index
        message_id: ID of the message containing this word
        """
        if not word or not message_id:
            return

        word = word.lower().strip()

        if len(word) < 3 or word in self.stop_words:
            return

        self.index[word].add(message_id)

    def index_message(self, message_id, text):
        """
        Indexes all words in a message.

        Args:
        message_id: Message ID
        text: Message text
        """
        if not message_id or message_id in self.processed_messages:
            return

        self.processed_messages.add(message_id)

        words, _ = self.process_text(text)

        for word in words:
            self.add_to_index(word, message_id)


    def get_index(self):
        return self.index

    def set_index(self, index):
        self.index = defaultdict(set)

        for word, message_ids in index.items():
            self.index[word] = set(message_ids)