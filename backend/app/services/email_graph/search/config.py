"""
Configuration pour le moteur de recherche.
"""

from enum import Enum

class SearchMode(Enum):
    """Modes de recherche disponibles"""
    CONTENT = "content"
    TEMPORAL = "temporal"
    USER = "user"
    COMBINED = "combined"

# Poids pour le scoring combiné
SCORING_WEIGHTS = {
    'content': 0.4,
    'temporal': 0.2,
    'user': 0.3,
    'graph': 0.1
}

# Configuration TF-IDF
TFIDF_CONFIG = {
    'min_term_length': 3,  # Longueur minimale des termes
    'pattern': r'\b[a-zA-Z0-9À-ÿ]{3,}\b',  # Pattern pour la tokenisation
    'subject_bonus': 0.5,  # Bonus si terme dans le sujet
    'freshness_decay_days': 30  # Decay temporel en jours
}

# Configuration du scoring temporel
TEMPORAL_CONFIG = {
    'default_hour': 23,
    'default_minute': 59
}

# Mapping des topics avec synonymes
TOPIC_MAPPINGS = {
    'facturation': ['facture', 'bill', 'billing', 'invoice'],
    'projet': ['project'],
    'ia': ['intelligence artificielle', 'ai'],
    'newsletter': ['actualités', 'news'],
    'meeting': ['réunion', 'meeting'],
    'important': ['important', 'urgent', 'critique'],
    'rapport': ['report', 'rapport']
}

# Configuration des snippets
SNIPPET_CONFIG = {
    'max_length': 150,
    'context_before': 50,
    'context_after': 100
}

# Configuration PageRank
PAGERANK_CONFIG = {
    'alpha': 0.85,
    'max_iter': 100,
    'tol': 1e-06
}