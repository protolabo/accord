"""
Calculateur de confiance pour les requêtes en langage naturel.

"""

from typing import List
from .types import ParsedEntity, IntentType
from backend.app.services.semantic_search.patterns import is_blacklisted_name


class ConfidenceCalculator:
    """
    Calcule un score de confiance global amélioré
    """

    def _calculate_overall_confidence(self, entities: List[ParsedEntity], intent: IntentType, language: str) -> float:
        """Calcule un score de confiance global amélioré - Code original inchangé"""

        if not entities:
            return 0.3  # Confiance faible sans entités

        # Moyenne pondérée des confiances des entités
        total_confidence = 0
        total_weight = 0

        for entity in entities:
            # Pondération selon le type d'entité
            weight = 1.0

            if entity.type == 'PERSON':
                # Pénaliser les noms suspects ou courts
                if is_blacklisted_name(entity.value, language) or len(entity.value) < 4:
                    weight = 0.3
                else:
                    weight = 1.0
            elif entity.type == 'EMAIL':
                weight = 1.2  # Emails sont très fiables
            elif entity.type == 'TEMPORAL':
                weight = 1.1  # Dates sont fiables
            elif entity.type == 'TOPIC':
                weight = 0.8  # Topics moins fiables
            elif entity.type == 'RECIPIENT_MARKER':
                weight = 0.9  # Marqueurs de destinataire fiables

            total_confidence += entity.confidence * weight
            total_weight += weight

        base_confidence = total_confidence / total_weight if total_weight > 0 else 0.3

        # Bonus conservateur pour intention spécifique
        intent_bonus = 0.1 if intent != IntentType.UNKNOWN else 0.0

        # Bonus pour diversité d'entités (mais modéré)
        entity_types = set(e.type for e in entities)
        diversity_bonus = min(0.1, len(entity_types) * 0.05)

        # Pénalité pour requêtes suspectes
        suspicious_penalty = 0
        for entity in entities:
            if entity.type == 'PERSON' and is_blacklisted_name(entity.value, language):
                suspicious_penalty -= 0.3
                break

        # Calculer le score final (plafonné à 0.9 pour éviter la surconfiance)
        final_confidence = base_confidence + intent_bonus + diversity_bonus + suspicious_penalty
        return max(0.1, min(0.9, final_confidence))