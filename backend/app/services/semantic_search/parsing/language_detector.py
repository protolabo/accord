"""
Détecteur de langue pour les requêtes en langage naturel.
"""

import re
from .base_parser import FRENCH_INDICATORS, ENGLISH_INDICATORS


class LanguageDetector:
    """
    Détecteur de langue
    """

    def _detect_language(self, query: str) -> str:
        """Détection de langue améliorée """
        query_lower = query.lower()

        # Compter les occurrences
        french_score = sum(1 for word in FRENCH_INDICATORS if word in query_lower)
        english_score = sum(1 for word in ENGLISH_INDICATORS if word in query_lower)

        # Ajuster les scores selon des patterns spécifiques
        if re.search(r"\b(d'|l'|qu'|c'est|n'est)\b", query_lower):
            french_score += 2

        if re.search(r"\b(it's|don't|can't|won't|i'm)\b", query_lower):
            english_score += 2

        # Décision finale
        if french_score > english_score:
            return 'fr'
        elif english_score > french_score:
            return 'en'
        else:
            return 'auto'  # Utiliser patterns multilingues