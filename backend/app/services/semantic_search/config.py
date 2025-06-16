"""
Configuration centralisée pour le service de recherche sémantique.
"""

from enum import Enum

class QueryType(str, Enum):
    """Types de requêtes supportées"""
    SEMANTIC = "semantic"
    CONTACT = "contact"
    TIME_RANGE = "time_range"
    TOPIC = "topic"
    THREAD = "thread"
    COMBINED = "combined"

class IntentType(Enum):
    """Types d'intention détectés dans les requêtes"""
    SEARCH_SEMANTIC = "search_semantic"
    SEARCH_CONTACT = "search_contact"
    SEARCH_TEMPORAL = "search_temporal"
    SEARCH_TOPIC = "search_topic"
    SEARCH_THREAD = "search_thread"
    SEARCH_ATTACHMENT = "search_attachment"
    SEARCH_COMBINED = "search_combined"
    UNKNOWN = "unknown"

# Configuration spaCy
SPACY_CONFIG = {
    'models_priority': ['fr_core_news_sm', 'en_core_web_sm'],
    'fallback_enabled': True,
    'min_confidence': 0.6
}

# Configuration de parsing
PARSING_CONFIG = {
    'min_query_length': 2,
    'max_query_length': 500,
    'confidence_threshold': 0.5,
    'default_limit': 10,
    'max_limit': 100
}

# Configuration des scores de confiance
CONFIDENCE_WEIGHTS = {
    'spacy_entity': 0.8,
    'pattern_match': 0.9,
    'intent_detection': 0.7,
    'entity_validation': 0.6
}

# Configuration temporelle
TEMPORAL_CONFIG = {
    'timezone_default': 'UTC',
    'date_formats': [
        '%Y-%m-%d',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S%z'
    ]
}

# Mapping des intentions vers les transformations
INTENT_TRANSFORMATION_MAP = {
    IntentType.SEARCH_SEMANTIC: QueryType.SEMANTIC,
    IntentType.SEARCH_CONTACT: QueryType.CONTACT,
    IntentType.SEARCH_TEMPORAL: QueryType.TIME_RANGE,
    IntentType.SEARCH_TOPIC: QueryType.TOPIC,
    IntentType.SEARCH_THREAD: QueryType.THREAD,
    IntentType.SEARCH_ATTACHMENT: QueryType.SEMANTIC,  # Fallback
    IntentType.SEARCH_COMBINED: QueryType.COMBINED,
    IntentType.UNKNOWN: QueryType.SEMANTIC
}

# Configuration des filtres par défaut
DEFAULT_FILTERS = {
    'limit': 10,
    'include_snippets': True,
    'similarity_threshold': 0.3
}

# Seuils de similarité par type de requête
SIMILARITY_THRESHOLDS = {
    QueryType.SEMANTIC: 0.4,
    QueryType.CONTACT: 0.2,
    QueryType.TIME_RANGE: 0.3,
    QueryType.TOPIC: 0.35,
    QueryType.THREAD: 0.3,
    QueryType.COMBINED: 0.25
}

# Limites par type de requête
QUERY_LIMITS = {
    QueryType.SEMANTIC: 15,
    QueryType.CONTACT: 20,
    QueryType.TIME_RANGE: 25,
    QueryType.TOPIC: 20,
    QueryType.THREAD: 10,
    QueryType.COMBINED: 30
}