from collections import defaultdict


def extract_keywords(text, subject="", max_keywords=3, stop_words=None):
    """
    Extract keywords from text using efficient NLP techniques.

    Args:
        text: Main text content
        subject: Subject line (given higher weight)
        max_keywords: Maximum number of keywords to extract
        stop_words: Set of stop words to filter out

    Returns:
        List of keywords
    """
    try:
        from nltk.tokenize import word_tokenize
    except ImportError:
        # Provide a fallback if NLTK is not available
        def word_tokenize(text):
            return text.split()

    # Set defaults if not provided
    if stop_words is None:
        stop_words = set()

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
                       word.lower() not in stop_words and
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
        if word.isalpha() and word.lower() not in stop_words and len(word) > 3:
            word_freq[word] += 3  # Subject words have higher importance

    # Sort by frequency and return top keywords
    sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in sorted_keywords[:max_keywords]]