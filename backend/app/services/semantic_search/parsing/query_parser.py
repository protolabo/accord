"""
Parser principal pour les requêtes en langage naturel - Version refactorisée.

Ce fichier orchestre tous les composants de parsing en utilisant les modules séparés,
mais conserve exactement la même interface et fonctionnalité que l'original.
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from .types import ParsedEntity, QueryContext, IntentType
from .base_parser import clean_query
from .language_detector import LanguageDetector
from .entity_extractor import EntityExtractor
from .intent_detector import IntentDetector
from .validator import EntityValidator
from .confidence_calculator import ConfidenceCalculator


class NaturalLanguageQueryParser:
    """
    Parseur principal pour les requêtes en langage naturel..
    """

    def __init__(self):
        """Initialise le parser avec tous ses composants """
        # Initialiser les composants modulaires
        self.language_detector = LanguageDetector()
        self.entity_extractor = EntityExtractor()
        self.intent_detector = IntentDetector()
        self.validator = EntityValidator()
        self.confidence_calculator = ConfidenceCalculator()

        # Charger les patterns (code original)
        self._load_patterns()

    def _load_patterns(self):
        """Charge les patterns enrichis"""
        from backend.app.services.semantic_search.patterns import get_patterns, get_stopwords

        # Charger tous les patterns en mode auto (FR + EN)
        self.all_patterns = get_patterns('auto', 'all')

        # Patterns spécifiques par langue
        self.patterns_fr = get_patterns('fr', 'all')
        self.patterns_en = get_patterns('en', 'all')

        # Stopwords
        self.stopwords_fr = get_stopwords('fr')
        self.stopwords_en = get_stopwords('en')
        self.stopwords_auto = get_stopwords('auto')

    def parse_query(self, query: str, context: QueryContext = None) -> Dict[str, Any]:
        """
        Parse une requête en langage naturel - Méthode principale originale conservée

        Args:
            query: Requête utilisateur
            context: Contexte optionnel

        Returns:
            Dictionnaire avec intention, entités et métadonnées
        """
        if not query or len(query.strip()) < 2:
            return self._empty_parse_result(query)

        # Détecter la langue en premier
        language = self.language_detector._detect_language(query)

        # Nettoyer la requête
        cleaned_query = clean_query(query)

        # Extraire les entités avec patterns adaptés à la langue
        entities = self.entity_extractor._extract_entities(cleaned_query, language)

        # Détecter l'intention
        intent = self.intent_detector._detect_intent(cleaned_query, entities, language)

        # Extraire les filtres
        filters = self._extract_filters(cleaned_query, entities, context)

        # Extraire le texte sémantique pur
        semantic_text = self._extract_semantic_text(cleaned_query, entities, language)

        # Calculer la confiance
        confidence = self.confidence_calculator._calculate_overall_confidence(entities, intent, language)

        return {
            'original_query': query,
            'cleaned_query': cleaned_query,
            'intent': intent.value,
            'semantic_text': semantic_text,
            'entities': [
                {
                    'type': e.type,
                    'value': e.value,
                    'original': e.original,
                    'confidence': e.confidence
                } for e in entities
            ],
            'filters': filters,
            'confidence': confidence,
            'language': language,
            'metadata': {
                'entity_count': len(entities),
                'has_temporal': any(e.type in ['TEMPORAL', 'DATE', 'TIME'] for e in entities),
                'has_person': any(e.type == 'PERSON' for e in entities),
                'has_email': any(e.type == 'EMAIL' for e in entities),
                'patterns_used': 'enriched_multilingual'
            }
        }

    def _extract_filters(self, query: str, entities: List[ParsedEntity], context: QueryContext = None) -> Dict[str, Any]:
        """Extrait les filtres avec support du contexte et négation"""
        filters = {}

        # Filtres temporels
        temporal_entities = [e for e in entities if e.type == 'TEMPORAL']
        if temporal_entities:
            # Gérer les plages de dates
            if len(temporal_entities) >= 2:
                # Trier par date
                dates = sorted([e.value for e in temporal_entities])
                filters['date_from'] = dates[0]
                filters['date_to'] = dates[-1]
            else:
                filters['date_from'] = temporal_entities[0].value

        # Gérer les plages temporelles complexes
        date_range_match = re.search(
            r'entre\s+le\s+(\d{1,2})\s+et\s+le\s+(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)',
            query, re.IGNORECASE
        )
        if date_range_match:
            start_day, end_day, month = date_range_match.groups()
            month_num = self._get_month_number(month)
            current_year = datetime.now().year
            filters['date_from'] = f"{current_year}-{month_num:02d}-{int(start_day):02d}"
            filters['date_to'] = f"{current_year}-{month_num:02d}-{int(end_day):02d}"

        # Filtres de contact
        email_entities = [e for e in entities if e.type == 'EMAIL']
        person_entities = [e for e in entities if e.type == 'PERSON']
        has_recipient_marker = any(e.type == 'RECIPIENT_MARKER' for e in entities)

        # Détecter si c'est un destinataire ou expéditeur
        query_lower = query.lower()
        is_recipient = (
            has_recipient_marker or
            any(pattern in query_lower for pattern in
                ['envoyé à', 'envoyés à', 'pour', 'à destination', 'sent to', 'for'])
        )
        is_sender = any(pattern in query_lower for pattern in
                       ['de', 'par', 'from', 'reçu de', 'received from'])

        if email_entities:
            if is_recipient:
                filters['recipient_email'] = email_entities[0].value
            else:
                filters['contact_email'] = email_entities[0].value
        elif person_entities:
            if is_recipient:
                filters['recipient_name'] = person_entities[0].value
            else:
                filters['contact_name'] = person_entities[0].value

        # Détection des états spéciaux
        if any(pattern in query_lower for pattern in ['envoyé', 'envoyés', 'boîte d\'envoi', 'sent', 'outbox']):
            filters['message_type'] = 'sent'
        elif any(pattern in query_lower for pattern in ['reçu', 'reçus', 'inbox', 'received']):
            filters['message_type'] = 'received'

        # Gestion de la négation et des actions
        action_patterns = self.all_patterns.get('action', {})
        for pattern, action_type in action_patterns.items():
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                if action_type == 'without_attachment':
                    filters['has_attachments'] = False
                elif action_type == 'without_importance':
                    filters['is_important'] = False
                elif action_type == 'sent_by_me':
                    filters['message_type'] = 'sent'
                elif action_type == 'received_by_me':
                    filters['message_type'] = 'received'
                elif action_type == 'has_attachment':
                    filters['has_attachments'] = True
                elif action_type == 'unread':
                    filters['is_unread'] = True
                elif action_type == 'important':
                    filters['is_important'] = True
                elif action_type == 'archived':
                    filters['is_archived'] = True

        # Types de pièces jointes spécifiques
        attachment_types = re.findall(r'\b(pdf|doc|docx|xls|xlsx|ppt|pptx|zip|jpg|png|gif)\b', query_lower)
        if attachment_types:
            filters['attachment_types'] = list(set(attachment_types))
            if 'has_attachments' not in filters:
                filters['has_attachments'] = True

        # Filtres de topic
        topic_entities = [e for e in entities if e.type == 'TOPIC']
        if topic_entities:
            filters['topic_ids'] = [e.value for e in topic_entities]

        return filters

    def _extract_semantic_text(self, query: str, entities: List[ParsedEntity], language: str) -> str:
        """Extrait le texte sémantique pur en supprimant les entités structurées"""

        # Commencer avec la requête nettoyée
        semantic_text = query

        # Supprimer les entités structurées détectées
        for entity in entities:
            if entity.type in ['EMAIL', 'TEMPORAL', 'PERSON', 'TOPIC', 'RECIPIENT_MARKER']:
                # Supprimer l'entité et son contexte immédiat
                pattern = re.escape(entity.original)
                semantic_text = re.sub(pattern, '', semantic_text, flags=re.IGNORECASE)

        # Supprimer les mots-outils selon la langue
        stopwords = self.stopwords_auto if language == 'auto' else (
            self.stopwords_fr if language == 'fr' else self.stopwords_en
        )

        for stopword in stopwords:
            pattern = r'\b' + re.escape(stopword) + r'\b'
            semantic_text = re.sub(pattern, '', semantic_text, flags=re.IGNORECASE)

        # Nettoyer les espaces multiples
        semantic_text = re.sub(r'\s+', ' ', semantic_text).strip()

        # Si le texte devient trop court, utiliser la requête originale
        if len(semantic_text) < 3:
            return query

        return semantic_text

    def _get_month_number(self, month_name: str) -> int:
        """Convertit un nom de mois en numéro"""
        from .base_parser import get_month_number
        return get_month_number(month_name)

    def _empty_parse_result(self, query: str) -> Dict[str, Any]:
        """Retourne un résultat vide pour requêtes invalides"""
        return {
            'original_query': query,
            'cleaned_query': '',
            'intent': IntentType.UNKNOWN.value,
            'semantic_text': query,
            'entities': [],
            'filters': {},
            'confidence': 0.1,
            'language': 'auto',
            'metadata': {
                'entity_count': 0,
                'has_temporal': False,
                'has_person': False,
                'has_email': False,
                'patterns_used': 'none'
            }
        }


# Instance singleton
_parser_instance: Optional[NaturalLanguageQueryParser] = None


def get_query_parser() -> NaturalLanguageQueryParser:
    """Récupère l'instance singleton du parser"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = NaturalLanguageQueryParser()
    return _parser_instance