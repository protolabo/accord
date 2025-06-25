"""
Détecteur d'intention pour les requêtes en langage naturel.

"""

import re
from typing import List
from .types import ParsedEntity, IntentType
from backend.app.services.semantic_search.patterns import get_patterns


class IntentDetector:
    """
    Détecteur d'intention 
    """

    def __init__(self):
        """Initialise le détecteur"""
        self._load_patterns()

    def _load_patterns(self):
        """Charge les patterns enrichis"""
        # Charger tous les patterns en mode auto (FR + EN)
        self.all_patterns = get_patterns('auto', 'all')

        # Patterns spécifiques par langue
        self.patterns_fr = get_patterns('fr', 'all')
        self.patterns_en = get_patterns('en', 'all')

    def _detect_intent(self, query: str, entities: List[ParsedEntity], language: str) -> IntentType:
        """Détecte l'intention principale avec patterns enrichis"""

        # Initialiser les scores
        intent_scores = {intent: 0.0 for intent in IntentType}

        # Sélectionner les patterns d'intention selon la langue
        if language == 'auto':
            intent_patterns = self.all_patterns.get('intent', {})
        else:
            patterns_data = self.patterns_fr if language == 'fr' else self.patterns_en
            intent_patterns = patterns_data.get('intent', {})

        # 1. Scoring basé sur les patterns spécifiques
        for intent_name, patterns_by_lang in intent_patterns.items():
            if intent_name in ['search_contact', 'search_temporal', 'search_attachment', 'search_thread']:
                intent_enum = getattr(IntentType, intent_name.upper(), IntentType.UNKNOWN)

                # Patterns pour la langue détectée
                patterns_list = patterns_by_lang.get(language, []) if language != 'auto' else []
                if language == 'auto':
                    # Combiner FR + EN
                    patterns_list.extend(patterns_by_lang.get('fr', []))
                    patterns_list.extend(patterns_by_lang.get('en', []))

                for pattern in patterns_list:
                    if re.search(pattern, query, re.IGNORECASE):
                        intent_scores[intent_enum] += 1.0

        # 2. Scoring basé sur les entités détectées
        entity_type_counts = {}
        for entity in entities:
            entity_type_counts[entity.type] = entity_type_counts.get(entity.type, 0) + 1

        for entity_type, count in entity_type_counts.items():
            if entity_type in ['EMAIL', 'PERSON', 'RECIPIENT_MARKER']:
                intent_scores[IntentType.SEARCH_CONTACT] += 0.8 * count
            elif entity_type == 'TEMPORAL':
                intent_scores[IntentType.SEARCH_TEMPORAL] += 0.8 * count
            elif entity_type == 'TOPIC':
                intent_scores[IntentType.SEARCH_TOPIC] += 0.6 * count

        # 3. Patterns d'action spécifiques
        action_patterns = self.all_patterns.get('action', {})
        for pattern, action_type in action_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                if action_type in ['has_attachment', 'without_attachment']:
                    intent_scores[IntentType.SEARCH_ATTACHMENT] += 1.2
                elif action_type == 'in_thread':
                    intent_scores[IntentType.SEARCH_THREAD] += 1.0

        # 4. Détection requête combinée
        unique_entity_types = set(e.type for e in entities)
        if len(unique_entity_types) >= 2:
            intent_scores[IntentType.SEARCH_COMBINED] += 0.5

        # Bonus si multiple patterns d'intention différents matchent
        active_intents = sum(1 for score in intent_scores.values() if score > 0)
        if active_intents >= 2:
            intent_scores[IntentType.SEARCH_COMBINED] += 0.3

        # 5. Sélection de l'intention avec le score le plus élevé
        best_intent = max(intent_scores.items(), key=lambda x: x[1])

        # Si aucun pattern spécifique détecté, default vers sémantique
        if best_intent[1] == 0:
            return IntentType.SEARCH_SEMANTIC

        return best_intent[0]