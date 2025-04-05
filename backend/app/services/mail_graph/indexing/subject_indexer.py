from collections import defaultdict
import re
from ..stopword import stopwords as mystopwords

class SubjectIndexer:

    def __init__(self):
        # Inverted index structure: term -> set of message IDs
        self.index = defaultdict(set)

        self.processed_messages = set()

        self.stop_words =  mystopwords()

        # Regex patterns to clean up topics
        self.re_patterns = [
            (r'^(re|fwd|fw|tr)(\[\d+\])?:\s*', ''),
            (r'\s+', ' ')
        ]

    def clean_subject(self, subject):
        if not subject:
            return ""

        cleaned = subject.lower().strip()

        for pattern, replacement in self.re_patterns:
            cleaned = re.sub(pattern, replacement, cleaned)

        return cleaned.strip()

    def tokenize_subject(self, subject):
        """
        Splits a subject line into terms.

        Args:
        subject: Subject line

        Returns:
        list: List of significant terms
        """
        if not subject:
            return []

        cleaned = self.clean_subject(subject)

        words = re.findall(r'\b\w+\b', cleaned)

        terms = [word for word in words if word not in self.stop_words and len(word) > 2]

        return terms

    def add_to_index(self, term, message_id):
        """
        Adds a term to the index for a specific message.

        Args:
        term: Term to index
        message_id: ID of the message containing this term
        """
        if not term or not message_id:
            return

        term = term.lower().strip()

        if len(term) < 3 or term in self.stop_words:
            return

        # add index
        self.index[term].add(message_id)

        # For subjects, also index prefixes for partial search
        if len(term) > 4:
            for i in range(3, min(len(term), 8)):
                prefix = term[:i]
                self.index[f"prefix:{prefix}"].add(message_id)

    def index_text(self, message_id, subject):
        """
        Indexes all terms in a subject line.

        Args:
        message_id: Message ID
        subject: Subject line
        """
        if not message_id or not subject or message_id in self.processed_messages:
            return


        self.processed_messages.add(message_id)


        clean_subject = self.clean_subject(subject)
        if clean_subject:
            # Index the full subject
            self.index["full:" + clean_subject].add(message_id)

        # Tokenize and index individual terms
        terms = self.tokenize_subject(subject)
        for term in terms:
            self.add_to_index(term, message_id)


    def get_index(self):
        return self.index

    def set_index(self, index):
        self.index = defaultdict(set)

        for term, message_ids in index.items():
            self.index[term] = set(message_ids)