import re
import uuid
import json
import os
import gc
from datetime import datetime
from collections import defaultdict
import numpy as np
import spacy

# Import NLP libraries with error handling
try:
    import sklearn
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import linear_kernel

    # Download NLTK resources if not already available
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('punkt')
        nltk.download('stopwords')


except ImportError:
    print("Warning: Some NLP libraries are missing. Topic extraction might be limited.")

""""
try:
    from spacy.lang.fr.stop_words import FRENCH_STOP_WORDS
    from spacy.lang.en.stop_words import ENGLISH_STOP_WORDS
    nlp_fr = spacy.load("fr_core_news_sm")
    nlp_en = spacy.load("en_core_web_sm")
    spacy_available = True
except LookupError:
    # Ccode for download spacy
    #spacy download fr_core_news_sm  # French language model
    #spacy download en_core_web_sm   # English language model (backup)
    print("Warning: spaCy language models not found.")
    spacy_available = False
"""
from spacy.lang.fr.stop_words import STOP_WORDS as FRENCH_STOP_WORDS
from spacy.lang.en.stop_words import STOP_WORDS as ENGLISH_STOP_WORDS
nlp_fr = spacy.load("fr_core_news_sm")
nlp_en = spacy.load("en_core_web_sm")
spacy_available = True


def profile_function(func):
    """Decorator to profile function execution time and memory usage."""
    import time
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        #print(f"Function {func.__name__} took {end_time - start_time:.2f} seconds to run")
        return result

    return wrapper


class OptimizedEmailGraphBuilder:
    """Optimized service to build a comprehensive email connection graph with memory efficiency."""

    def __init__(self, central_user_email=None, output_dir="./graph_output"):
        """
        Initialize the graph builder with an optional central user.

        Args:
            central_user_email: The email of the central user for the graph
            output_dir: Directory to store intermediate and final output
        """
        # Node collections
        self.users = {}  # email -> user_node
        self.messages = {}  # message_id -> message_node
        self.threads = {}  # thread_id -> thread_node
        self.topics = {}  # topic_id -> topic_node
        self.relations = []  # list of all relations/edges

        # Special collection for tracking connection strength
        self.connection_strength = {}  # email -> strength score

        # Cache for expensive operations - initialize this BEFORE using _normalize_email
        self._email_normalization_cache = {}
        self.message_vectors = {}

        # Set up output directory
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Store the central user's email (normalized)
        self.central_user_email = self._normalize_email(central_user_email) if central_user_email else None
        self.central_user_node = None  # Will store the node of the central user

        # Initialize stopwords for topic extraction
        try:
            self.stop_words = set(stopwords.words('french'))
        except:
            self.stop_words = set()

        # for spacy
        self.word_index = {}  # words : {message_id}
        self.entity_index = {}  # entity : {message_id}
        self.subject_index = {}  # word : {message_id}

        # temp
        spacy_available = True

        # Initialize spaCy and stopwords
        self.spacy_available = spacy_available

        # Combine spaCy's stopwords with custom ones
        if spacy_available:
            self.stop_words = FRENCH_STOP_WORDS
            self.stop_words.update(ENGLISH_STOP_WORDS)
        else:
            self.stop_words = set()

        # Add custom stopwords for emails
        self.custom_stopwords = {
                # French email-specific stopwords
                "bonjour", "cordialement", "merci", "salutations", "cdt", "bien",
                "salut", "madame", "monsieur", "cher", "chère", "cheres", "chers",
                "a", "à", "au", "aux", "avec", "ce", "ces", "dans", "de", "des",
                "du", "en", "entre", "et", "il", "ils", "je", "j'ai", "la", "le",
                "les", "leur", "lui", "ma", "mais", "me", "même", "mes", "moi",
                "mon", "nos", "notre", "nous", "ou", "par", "pas", "pour", "qu",
                "que", "qui", "s", "sa", "se", "si", "son", "sur", "ta", "te",
                "tes", "toi", "ton", "tu", "un", "une", "vos", "votre", "vous",

                # English common email terms (for mixed-language emails)
                "hello", "hi", "thanks", "thank", "you", "regards", "sincerely",
                "best", "attachment", "please", "file", "files", "dear", "kind",
                "regards", "sincerely", "best", "attachment", "please"
            
                #email stop words
                'fw', 're', 'fwd', 'reply', 'sent', 'from', 'to', 'cc',
                'bcc','subject', 'date', 'hello', 'hi', 'thanks', 'thank', 'you', 'regards',
                'sincerely', 'best', 'attachment', 'please', 'file', 'files'
        }

        #even if it's short keep them
        self.important_terms = {"pdf","vpn"}

        self.min_word_length = 3

        self.stop_words.update(self.custom_stopwords)


    def _normalize_email(self, email):
        """
        Normalize an email address for consistent comparison with caching for performance.
        """
        if not email:
            return ""

        # Check cache first. if yes , it's already normalized
        if email in self._email_normalization_cache:
            return self._email_normalization_cache[email]

        # Extract email from "Name <email@domain>" format
        if '<' in email and '>' in email:
            try:
                email = re.search(r'<([^>]+)>', email).group(1)
            except (AttributeError, IndexError):
                print(f"Could not parse email address: {email}")
                return None  # Fall back to the original email if regex fails

        normalized = email.lower().strip()

        # Store in cache
        self._email_normalization_cache[email] = normalized
        return normalized

    def _update_connection_strength(self, email, weight=1):
        """
        Update the connection strength to the central user.
        """
        if not self.central_user_email or not email:
            return

        # Normalize email
        email = self._normalize_email(email)

        # Update strength
        self.connection_strength[email] = self.connection_strength.get(email, 0) + weight

    @staticmethod
    def extract_email_parts(email):
        """
        Extract domain, name, etc. from an email address.
        """
        if not email:
            return None, None, None

        # Extract domain
        try:
            domain_match = re.search(r'@([^@]+)$', email)
            domain = domain_match.group(1) if domain_match else None
        except (AttributeError, IndexError):
            domain = None

        # Extract username
        try:
            name_match = re.search(r'^([^@]+)@', email)
            username = name_match.group(1) if name_match else None
        except (AttributeError, IndexError):
            username = None

        # Build name from username
        parts = username.split('.') if username else []
        name = ' '.join([p.capitalize() for p in parts if p]) if parts else None

        return email, domain, name

    def get_or_create_user(self, email_address):
        """
        Get or create a user node with minimal overhead.
        """
        if not email_address:
            # exit() ?
            return None

        # Extract email if in "Name <email@domain.com>" format
        # for example :  "DUPONT@ACME.COM" ->  "dupont@acme.com"
        clean_email = self._normalize_email(email_address)

        # Check if user already exists
        if clean_email in self.users:
            return self.users[clean_email]

        # Extract email parts
        email, domain, name = self.extract_email_parts(email_address)

        # Create a new user
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "type": "user",
            "email": clean_email,
            "name": name,
            "domain": domain,
            "is_central_user": clean_email == self.central_user_email,
            "connection_strength": 0
        }

        self.users[clean_email] = user

        # If this is the central user, store the reference (optimisation de performance)
        if clean_email == self.central_user_email:
            self.central_user_node = user

        return user

    @profile_function
    def create_message_node(self, email_data):
        """
        Create a message node from email data with memory efficiency in mind.
        """
        message_id = email_data.get("Message-ID")
        if not message_id:
            return None

        # Check if message already exists
        if message_id in self.messages:
            return self.messages[message_id]

        # Convert date to datetime format if it's a string
        date_str = email_data.get("Internal-Date")

        date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))


        # Check if this message involves the central user - use cached normalization
        from_email = self._normalize_email(email_data.get("From", ""))

        # Get recipient lists only once to avoid redundant splitting
        to_list = email_data.get("To", "").split(",") if email_data.get("To") else []
        cc_list = email_data.get("Cc", "").split(",") if email_data.get("Cc") else []
        bcc_list = email_data.get("Bcc", "").split(",") if email_data.get("Bcc") else []

        # Filter empty entries and normalize only once
        to_emails = [self._normalize_email(e) for e in to_list if e.strip()]
        cc_emails = [self._normalize_email(e) for e in cc_list if e.strip()]
        bcc_emails = [self._normalize_email(e) for e in bcc_list if e.strip()]

        # Create a new message with minimal data
        # il n'y aura pas la sauvegarde du message donc supprimer le body_plain , body_html, snippet
        message = {"id": message_id, "type": "message", "thread_id": email_data.get("Thread-ID", ""),
                   "date": date.isoformat(), "labels": email_data.get("Labels", []),
                   "categories": email_data.get("Categories", []),
                   "has_attachment": bool(email_data.get("Attachments", [])),
                   "attachment_count": len(email_data.get("Attachments", [])), "from": from_email, "to": to_emails,
                   "cc": cc_emails, "bcc": bcc_emails}

        #"body_plain": body_plain, "body_html": body_html
        #"subject": email_data.get("Subject", ""), "snippet": email_data.get("Snippet", "")

        self.messages[message_id] = message

        # Create or update the thread
        # thread by gmail and not by accord
        self.get_or_create_thread(email_data)

        return message

    @profile_function
    def extract_topics(self, email_data):
        """
        Extract topics with memory efficiency in mind.
        """

        # Use subject and snippet instead of full body to save memory
        subject = email_data.get("Subject", "")
        body_plain = email_data.get("Body", {}).get("plain", "")

        # Use snippet as fallback if subject is empty
        text = body_plain if body_plain else subject
        if not text:
            return []

        # Extract keywords with reduced count to save processing
        keywords = self._extract_keywords(text, subject, max_keywords=3)

        # Create topic nodes
        topics = []
        for keyword in keywords:
            topic_id = keyword.lower()

            if topic_id in self.topics:
                topic = self.topics[topic_id]
                topic["message_count"] += 1
            else:
                topic = {
                    "id": topic_id,
                    "type": "topic",
                    "name": keyword,
                    "message_count": 1,
                    "relevance_to_central_user": 0
                }
                self.topics[topic_id] = topic

            # Mark as relevant to central user if needed
            message_id = email_data.get("Message-ID")
            message = self.messages.get(message_id)
            if message and message.get("involves_central_user", False):
                topic["relevance_to_central_user"] += 1

            topics.append(topic)

        return topics

    def _extract_keywords(self, text, subject="", max_keywords=3):
        """
        Extract keywords from text using efficient NLP techniques.
        Reduced max_keywords to save memory.
        """
        # Skip if NLTK is not available
        if 'nltk' not in globals():
            return []

        # Preprocess text
        text = text.lower()

        # Tokenize text efficiently
        try:
            tokens = word_tokenize(text)
        except:
            # Fallback if NLTK fails
            tokens = text.split()

        # Remove stopwords and short/non-alphabetic tokens
        filtered_tokens = [word for word in tokens if
                           word.isalpha() and
                           word.lower() not in self.stop_words and
                           len(word) > 3]

        # Count word frequencies
        word_freq = defaultdict(int)
        for word in filtered_tokens:
            word_freq[word] += 1

        # Give extra weight to words in subject
        try:
            subject_tokens = word_tokenize(subject.lower()) if subject else []
        except:
            # Fallback if NLTK fails
            subject_tokens = subject.lower().split() if subject else []

        for word in subject_tokens:
            if word.isalpha() and word.lower() not in self.stop_words and len(word) > 3:
                word_freq[word] += 3  # Subject words have higher importance

        # Sort by frequency and return top keywords
        sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_keywords[:max_keywords]]

    @profile_function
    def get_or_create_thread(self, email_data):
        """
        Get or create a thread node with memory efficiency in mind.
        """
        thread_id = email_data.get("Thread-ID", "")
        if not thread_id:
            return None

        # Check if thread already exists
        if thread_id in self.threads:
            thread = self.threads[thread_id]

            # Update participants
            from_email = email_data.get("From", "")
            to_emails = email_data.get("To", "").split(",") if email_data.get("To") else []
            cc_emails = email_data.get("Cc", "").split(",") if email_data.get("Cc") else []

            # Create a set of participants (more memory efficient than repeated string operations)
            participants = set(thread["participants"])

            if from_email:
                participants.add(from_email)

            for email in to_emails + cc_emails:
                if email and email.strip():
                    participants.add(email.strip())

            thread["participants"] = list(participants)
            thread["message_count"] = thread.get("message_count", 0) + 1

            # Update last message date if needed
            date = datetime.fromisoformat(email_data["Internal-Date"].replace('Z', '+00:00'))
            thread["last_message_date"] = max(thread.get("last_message_date", ""), date.isoformat())

            return thread

        # Create a new thread
        # subject ??
        thread = {
            "id": thread_id,
            "type": "thread",
            "subject": email_data.get("Subject", ""),
            "participants": [],
            "message_count": 1,
            "last_message_date": "",
            "categories": [],
            "topics": []
        }

        # Add participants efficiently
        from_email = email_data.get("From", "")
        to_emails = email_data.get("To", "").split(",") if email_data.get("To") else []
        cc_emails = email_data.get("Cc", "").split(",") if email_data.get("Cc") else []

        participants = set()

        if from_email:
            participants.add(from_email)

        for email in to_emails + cc_emails:
            if email and email.strip():
                participants.add(email.strip())

        thread["participants"] = list(participants)

        # Set last message date
        date = datetime.fromisoformat(email_data["Internal-Date"].replace('Z', '+00:00'))
        thread["last_message_date"] = date.isoformat()

        self.threads[thread_id] = thread
        return thread

    @profile_function
    def create_relation(self, source, target, relation_type, email_data=None, weight=1, metadata=None):
        """
        Create a relation between two nodes with memory efficiency in mind.
        """

        # Validate that source and target have IDs
        if not source.get("id") or not target.get("id"):
            return None

        # Create a minimal relation object
        relation = {
            "id": str(uuid.uuid4()),
            "type": "relation",
            "source_id": source["id"],
            "target_id": target["id"],
            "relation_type": relation_type,
            "weight": weight,
        }

        # Add optional email data if provided (minimal info only)
        if email_data:
            relation["message_id"] = email_data.get("Message-ID", "")
            relation["thread_id"] = email_data.get("Thread-ID", "")
            if relation_type in ["SENT", "RECEIVED", "REPLIED_TO"]:
                relation["date"] = email_data.get("Internal-Date", "")

        #  any critical metadata only if needed in future
        if metadata:
            essential_metadata = {}
            for key, value in metadata.items():
                if key in ["accord_thread_id", "accord_thread_label","accord_thread_name"] :
                    essential_metadata[key] = value


        self.relations.append(relation)
        return relation

    def create_message_topic_relation(self, message, topic, weight=1.0):
        """
        Create a minimal relation between a message and a topic.
        """
        relation = {
            "id": str(uuid.uuid4()),
            "type": "relation",
            "source_id": message["id"],
            "target_id": topic["id"],
            "relation_type": "HAS_TOPIC",
            "weight": weight,
            "involves_central_user": message.get("involves_central_user", False)
        }

        self.relations.append(relation)
        return relation

    def _get_language_model(self, text):
        """
        Determine which language model to use based on text content.
        Defaults to French if uncertain.
        """
        if not self.spacy_available:
            return None

        # Simple heuristic for language detection
        # Count common French words vs English words
        french_indicators = ["le", "la", "les", "un", "une", "et", "pour", "dans", "avec"]
        english_indicators = ["the", "a", "an", "and", "for", "in", "with", "to", "of"]

        text_lower = text.lower()
        fr_count = sum(1 for word in french_indicators if f" {word} " in f" {text_lower} ")
        en_count = sum(1 for word in english_indicators if f" {word} " in f" {text_lower} ")

        return nlp_fr if fr_count >= en_count else nlp_en

    @profile_function
    def _process_text_with_spacy(self, text, is_subject=False):
        """
        Process text with spaCy to extract tokens, lemmas and entities.

        Args:
            text: Text to process
            is_subject: Whether this is a subject line (for special handling)

        Returns:
            tokens, entities (lists of strings)
        """
        if not text or not self.spacy_available:
            return [], []

        # Select language model
        nlp = self._get_language_model(text)
        if not nlp:
            # Fallback for when spaCy is not available
            return self._fallback_text_processing(text)

        # Process the text
        doc = nlp(text)

        # Extract tokens (excluding stopwords and punctuation)
        tokens = []
        for token in doc:
            # Get the lemma (base form) of the token
            lemma = token.lemma_.lower().strip()

            # Keep token if:
            # 1. It's in our important terms, OR
            # 2. It's a subject and longer than 1 character (subjects get special treatment), OR
            # 3. It's longer than min_word_length, not a stopword, not punctuation
            if (lemma in self.important_terms or
                    (is_subject and len(lemma) > 1) or
                    (len(lemma) >= self.min_word_length and
                     lemma not in self.stop_words and
                     not token.is_punct and not token.is_space)):
                tokens.append(lemma)

        # Extract named entities (these are often important regardless of length)
        entities = []
        for ent in doc.ents:
            if len(ent.text) > 1:  # Ignore single-character entities
                entities.append(ent.text.lower())

        return tokens, entities

    def _fallback_text_processing(self, text):
        """Fallback method when spaCy is not available."""
        # Basic tokenization
        tokens = re.findall(r'\b\w+\b', text.lower())

        # Filter short words and stopwords
        filtered_tokens = []
        for token in tokens:
            if token in self.important_terms or (len(token) >= self.min_word_length and token not in self.stop_words):
                filtered_tokens.append(token)

        return filtered_tokens, []

    @profile_function
    def index_message(self, message_id, subject, body_text):
        """
        Index a message's content using spaCy for intelligent analysis.

        Args:
            message_id: ID of the message
            subject: Subject line
            body_text: Body text of the message
        """
        if not subject and not body_text:
            return

        # Process subject with special handling
        subject_tokens, subject_entities = self._process_text_with_spacy(subject, is_subject=True)

        # Process body
        body_tokens, body_entities = self._process_text_with_spacy(body_text)

        # Add to word index (combining subject and body tokens)
        all_tokens = set(subject_tokens + body_tokens)
        for token in all_tokens:
            if token not in self.word_index:
                self.word_index[token] = set()
            self.word_index[token].add(message_id)

        # Add to subject-specific index
        for token in subject_tokens:
            if token not in self.subject_index:
                self.subject_index[token] = set()
            self.subject_index[token].add(message_id)

        # Add to entity index
        all_entities = set(subject_entities + body_entities)
        for entity in all_entities:
            if entity not in self.entity_index:
                self.entity_index[entity] = set()
            self.entity_index[entity].add(message_id)

    @profile_function
    def process_email(self, email_data):
        """
        Process an email and add nodes and relations to the graph with memory efficiency in mind.
        """
        try:
            # Create message node
            message = self.create_message_node(email_data)
            if not message:
                return False

            # Extract text for indexing
            subject = email_data.get("Subject", "")
            body_plain = email_data.get("Body", {}).get("plain", "")

            # Index the message content
            self.index_message(message["id"], subject, body_plain)

            # Process sender (From)
            from_user = self.get_or_create_user(email_data["From"])
            if from_user:
                # Create SENT relation
                self.create_relation(from_user, message, "SENT", email_data)

                # If central user is the sender, create a special relation
                if from_user.get("is_central_user"):
                    self.create_relation(from_user, message, "SENT_BY_CENTRAL_USER", email_data, weight=3)

            # Process recipients (To)
            to_emails = email_data["To"].split(",") if email_data["To"] else []
            for email in to_emails:
                if not email.strip():
                    continue

                to_user = self.get_or_create_user(email.strip())
                if to_user:
                    # Create RECEIVED relation
                    self.create_relation(message, to_user, "RECEIVED", email_data)

                    # Create EMAILED relation between users
                    if from_user:
                        self.create_relation(from_user, to_user, "EMAILED", email_data)

                        # Update connection strength for both users if central user involved
                        if from_user.get("is_central_user"):
                            self._update_connection_strength(email.strip(), weight=2)
                            to_user["connection_strength"] = to_user.get("connection_strength", 0) + 2
                        elif to_user.get("is_central_user"):
                            self._update_connection_strength(email_data["From"], weight=2)
                            from_user["connection_strength"] = from_user.get("connection_strength", 0) + 2

            # Process CC recipients
            cc_emails = email_data["Cc"].split(",") if email_data["Cc"] else []
            for email in cc_emails:
                if not email.strip():
                    continue

                cc_user = self.get_or_create_user(email.strip())
                if cc_user:
                    # Create CC relation
                    self.create_relation(message, cc_user, "CC", email_data)

                    # Create EMAILED_CC relation if central user is involved
                    if from_user and (from_user.get("is_central_user") or cc_user.get("is_central_user")):
                        self.create_relation(from_user, cc_user, "EMAILED_CC", email_data)

                        # Update connection strength
                        if from_user.get("is_central_user"):
                            self._update_connection_strength(email.strip(), weight=1)
                            cc_user["connection_strength"] = cc_user.get("connection_strength", 0) + 1
                        elif cc_user.get("is_central_user"):
                            self._update_connection_strength(email_data["From"], weight=1)
                            from_user["connection_strength"] = from_user.get("connection_strength", 0) + 1

            # Process BCC recipients (only if central user is involved - to save processing)
            if self.central_user_email:
                bcc_emails = email_data["Bcc"].split(",") if email_data["Bcc"] else []
                for email in bcc_emails:
                    if not email.strip():
                        continue

                    bcc_user = self.get_or_create_user(email.strip())
                    if bcc_user:
                        # Create BCC relation
                        self.create_relation(message, bcc_user, "BCC", email_data)

                        # Create EMAILED_BCC relation
                        if from_user and (from_user.get("is_central_user") or bcc_user.get("is_central_user")):
                            self.create_relation(from_user, bcc_user, "EMAILED_BCC", email_data)

                            # Update connection strength
                            if from_user.get("is_central_user"):
                                self._update_connection_strength(email.strip(), weight=1)
                                bcc_user["connection_strength"] = bcc_user.get("connection_strength", 0) + 1
                            elif bcc_user.get("is_central_user"):
                                self._update_connection_strength(email_data["From"], weight=1)
                                from_user["connection_strength"] = from_user.get("connection_strength", 0) + 1


            topics = self.extract_topics(email_data)
            for topic in topics:
                self.create_message_topic_relation(message, topic)
                # Add topic to the thread's topic list
                thread_id = message.get("thread_id")
                if thread_id and thread_id in self.threads:
                    thread = self.threads[thread_id]
                    if "topics" not in thread:
                        thread["topics"] = []
                    # Add topic if not already in the list
                    topic_name = topic["name"]
                    if topic_name not in thread["topics"]:
                        thread["topics"].append(topic_name)
            return True
        except Exception as e:
            print(f"Error processing email {email_data.get('Message-ID')}: {str(e)}")
            return False

    @profile_function
    def process_thread_relations(self):
        """
        Create relations between messages in the same thread with memory efficiency in mind.
        Only processes threads with multiple messages.
        """
        # Group messages by thread_id (with memory efficiency)
        thread_messages = defaultdict(list)
        processed_threads = 0

        # First pass - count threads with multiple messages
        for message_id, message in self.messages.items():
            thread_id = message.get("thread_id")
            if thread_id:
                thread_messages[thread_id].append(message_id)

        # Log progress metrics
        thread_count = len(thread_messages)
        multi_message_threads = sum(1 for msgs in thread_messages.values() if len(msgs) > 1)
        print(
            f"Processing {multi_message_threads} threads with multiple messages (out of {thread_count} total threads)")

        # Process threads with multiple messages
        for thread_id, message_ids in thread_messages.items():
            if len(message_ids) <= 1:
                continue  # Skip threads with only one message

            # Get actual messages
            messages = [self.messages[mid] for mid in message_ids if mid in self.messages]
            if len(messages) <= 1:
                continue

            # Sort messages by date
            sorted_messages = sorted(messages, key=lambda x: x.get("date", ""))

            # Create PART_OF_THREAD relations
            for message in sorted_messages:
                if thread_id in self.threads:
                    thread = self.threads[thread_id]
                    relation = {
                        "id": str(uuid.uuid4()),
                        "type": "relation",
                        "source_id": message["id"],
                        "target_id": thread["id"],
                        "relation_type": "PART_OF_THREAD",
                        "weight": 1,
                    }
                    self.relations.append(relation)

            # Create REPLIED_TO relations
            for i in range(1, len(sorted_messages)):
                previous = sorted_messages[i - 1]
                current = sorted_messages[i]


            # create replied_to connexion
            relation = {
                    "id": str(uuid.uuid4()),
                    "type": "relation",
                    "source_id": current["id"],
                    "target_id": previous["id"],
                    "relation_type": "REPLIED_TO",
                    "weight": 1,
                }
            self.relations.append(relation)

            # create central user conversation
            central_relation = {
                        "id": str(uuid.uuid4()),
                        "type": "relation",
                        "source_id": current["id"],
                        "target_id": previous["id"],
                        "relation_type": "CENTRAL_USER_CONVERSATION",
                        "weight": 3,
                    }
            self.relations.append(central_relation)

            processed_threads += 1
            if processed_threads % 100 == 0:
                print(f"Processed {processed_threads}/{multi_message_threads} multi-message threads")

    def _serialize_node(self, node):
        """Convert a node to a JSON-serializable format."""
        import copy
        node_copy = copy.deepcopy(node)

        # Convert any non-serializable values
        for key, value in node_copy.items():
            if isinstance(value, (set, frozenset)):
                node_copy[key] = list(value)
            elif isinstance(value, np.ndarray):
                node_copy[key] = value.tolist()

        return node_copy

    def save_indices(self):
        """Save the word, entity and subject indices to files."""
        indices_dir = os.path.join(self.output_dir, "indices")
        os.makedirs(indices_dir, exist_ok=True)

        # Helper function to make sets JSON-serializable
        def serialize(index):
            return {key: list(values) for key, values in index.items()}

        # Save all indices
        with open(os.path.join(indices_dir, "word_index.json"), 'w') as f:
            json.dump(serialize(self.word_index), f)

        with open(os.path.join(indices_dir, "entity_index.json"), 'w') as f:
            json.dump(serialize(self.entity_index), f)

        with open(os.path.join(indices_dir, "subject_index.json"), 'w') as f:
            json.dump(serialize(self.subject_index), f)

    def load_indices(self):
        """Load indices from files."""
        indices_dir = os.path.join(self.output_dir, "indices")
        if not os.path.exists(indices_dir):
            return

        # Helper function to convert lists back to sets
        def deserialize(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
                return {key: set(values) for key, values in data.items()}

        try:
            self.word_index = deserialize(os.path.join(indices_dir, "word_index.json"))
            self.entity_index = deserialize(os.path.join(indices_dir, "entity_index.json"))
            self.subject_index = deserialize(os.path.join(indices_dir, "subject_index.json"))
        except Exception as e:
            print(f"Error loading indices: {str(e)}")

    @profile_function
    def build_graph_two_phase(self, emails):
        """Build the graph in two phases to reduce memory usage."""
        print(f"Building graph for {len(emails)} emails using two-phase approach...")

        # Phase 1: Basic structure building
        print("Phase 1: Building basic graph structure...")

        # Reset the graph
        self.users = {}
        self.messages = {}
        self.threads = {}
        self.topics = {}
        self.relations = []
        self.connection_strength = {}

        #Reset indices
        self.word_index = {}
        self.entity_index = {}
        self.subject_index = {}

        # Pre-create the central user

        #get or create central user
        self.central_user_node = self.get_or_create_user(self.central_user_email)

        # marque le noeud comme central user
        print(f"Central user initialized: {self.central_user_email}")

        # Process in batches
        batch_size = 5000
        processed_count = 0

        for i in range(0, len(emails), batch_size):
            end = min(i + batch_size, len(emails))
            print(f"Processing emails {i}-{end}...")

            batch_processed = 0
            for email in emails[i:end]:
                if self.process_email(email):
                    batch_processed += 1
                    processed_count += 1

            print(f"Batch completed: {batch_processed} processed")

            # Force garbage collection
            gc.collect()

        # Save basic structure


        users_file = os.path.join(self.output_dir, "users.json")
        with open(users_file, 'w', encoding='utf-8') as f:
            json.dump({k: self._serialize_node(v) for k, v in self.users.items()}, f, ensure_ascii=False)

        messages_file = os.path.join(self.output_dir, "messages.json")
        with open(messages_file, 'w', encoding='utf-8') as f:
            json.dump({k: self._serialize_node(v) for k, v in self.messages.items()}, f, ensure_ascii=False)

        threads_file = os.path.join(self.output_dir, "threads.json")
        with open(threads_file, 'w', encoding='utf-8') as f:
            json.dump({k: self._serialize_node(v) for k, v in self.threads.items()}, f, ensure_ascii=False)

        topics_file = os.path.join(self.output_dir, "topics.json")
        with open(topics_file, 'w', encoding='utf-8') as f:
            json.dump({k: self._serialize_node(v) for k, v in self.topics.items()}, f, ensure_ascii=False)

        print("saving indices...")
        self.save_indices()

        print(f"Phase 1 complete. Basic structure saved.")

        # Phase 2: Thread relations
        print("Phase 2: Processing thread relations...")
        self.process_thread_relations()

        # Save thread relations
        thread_relations_file = os.path.join(self.output_dir, "thread_relations.json")
        with open(thread_relations_file, 'w', encoding='utf-8') as f:
            json.dump([self._serialize_node(r) for r in self.relations], f, ensure_ascii=False)

        # Clear relations to free memory
        thread_relations_count = len(self.relations)
        self.relations = []
        gc.collect()

        # Phase 3: Content similarity (most memory intensive)
        print("Phase 3: getting accord thread...")
        # To do

        # Save similarity relations
        similarity_relations_file = os.path.join(self.output_dir, "similarity_relations.json")
        with open(similarity_relations_file, 'w', encoding='utf-8') as f:
            json.dump([self._serialize_node(r) for r in self.relations], f, ensure_ascii=False)

        content_relations_count = len(self.relations)

        # Save final metadata
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "total_emails_processed": processed_count,
            "users_count": len(self.users),
            "messages_count": len(self.messages),
            "threads_count": len(self.threads),
            "topics_count": len(self.topics),
            "thread_relations_count": thread_relations_count,
            "content_relations_count": content_relations_count,
            "total_relations_count": thread_relations_count + content_relations_count,
            "central_user_email": self.central_user_email,
            "output_files": {
                "users": users_file,
                "messages": messages_file,
                "threads": threads_file,
                "topics": topics_file,
                "thread_relations": thread_relations_file,
            }
        }

        metadata_file = os.path.join(self.output_dir, "metadata.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False)

        print(f"Graph building complete.")
        print(f"- {metadata['users_count']} users")
        print(f"- {metadata['messages_count']} messages")
        print(f"- {metadata['threads_count']} threads")
        print(f"- {metadata['topics_count']} topics")
        print(f"- {metadata['total_relations_count']} total relations")
        print(f"Results saved to {self.output_dir}")

        return metadata