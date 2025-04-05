import re


def get_language_model(text, nlp_fr=None, nlp_en=None):
    """
    Determine which language model to use based on text content.
    Defaults to French if uncertain.

    Args:
        text: Text to analyze
        nlp_fr: French language model
        nlp_en: English language model

    Returns:
        Language model to use
    """
    if not nlp_fr or not nlp_en:
        return None

    # Simple heuristic for language detection
    # Count common French words vs English words
    french_indicators = ["le", "la", "les", "un", "une", "et", "pour", "dans", "avec"]
    english_indicators = ["the", "a", "an", "and", "for", "in", "with", "to", "of"]

    text_lower = text.lower()
    fr_count = sum(1 for word in french_indicators if f" {word} " in f" {text_lower} ")
    en_count = sum(1 for word in english_indicators if f" {word} " in f" {text_lower} ")

    return nlp_fr if fr_count >= en_count else nlp_en


def process_text_with_spacy(text, is_subject=False, nlp=None, stop_words=None, important_terms=None, min_word_length=3):
    """
    Process text with spaCy to extract tokens, lemmas and entities.

    Args:
        text: Text to process
        is_subject: Whether this is a subject line (for special handling)
        nlp: Language model to use
        stop_words: Set of stop words to filter out
        important_terms: Set of important terms to always include
        min_word_length: Minimum word length to consider

    Returns:
        tokens, entities (lists of strings)
    """
    if not text or not nlp:
        return [], []

    # Set defaults if not provided
    if stop_words is None:
        stop_words = set()
    if important_terms is None:
        important_terms = set()

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
        if (lemma in important_terms or
                (is_subject and len(lemma) > 1) or
                (len(lemma) >= min_word_length and
                 lemma not in stop_words and
                 not token.is_punct and not token.is_space)):
            tokens.append(lemma)

    # Extract named entities (these are often important regardless of length)
    entities = []
    for ent in doc.ents:
        if len(ent.text) > 1:  # Ignore single-character entities
            entities.append(ent.text.lower())

    return tokens, entities


def fallback_text_processing(text, stop_words=None, important_terms=None, min_word_length=3):
    """
    Fallback method when spaCy is not available.

    Args:
        text: Text to process
        stop_words: Set of stop words to filter out
        important_terms: Set of important terms to always include
        min_word_length: Minimum word length to consider

    Returns:
        tokens, empty_entities
    """
    # Set defaults if not provided
    if stop_words is None:
        stop_words = set()
    if important_terms is None:
        important_terms = set()

    # Basic tokenization
    tokens = re.findall(r'\b\w+\b', text.lower())

    # Filter short words and stopwords
    filtered_tokens = []
    for token in tokens:
        if token in important_terms or (len(token) >= min_word_length and token not in stop_words):
            filtered_tokens.append(token)

    return filtered_tokens, []