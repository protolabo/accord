"""
Transformateur de requêtes simplifié utilisant uniquement spaCy et les patterns.
"""

import time
from typing import Dict, Any

from ..config import (
    INTENT_TRANSFORMATION_MAP, SIMILARITY_THRESHOLDS, QUERY_LIMITS,
    DEFAULT_FILTERS, CONFIDENCE_WEIGHTS, IntentType, QueryType
)
from ..services.parsing_service import NLPParsingService
from ..services.validation_service import QueryValidationService
from ..services.transformation_service import TransformationService


class QueryTransformationStrategy:
    """Stratégies de transformation basées sur le type d'intention"""

    @staticmethod
    def transform_semantic(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transformation pour requête sémantique pure"""
        return {
            'query_type': QueryType.SEMANTIC,
            'semantic_text': parsed_data.get('semantic_text', ''),
            'filters': QueryTransformationStrategy._extract_basic_filters(parsed_data),
            'similarity_threshold': SIMILARITY_THRESHOLDS[QueryType.SEMANTIC],
            'limit': QUERY_LIMITS[QueryType.SEMANTIC],
            'include_snippets': True
        }

    @staticmethod
    def transform_contact(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transformation pour recherche de contact"""
        filters = QueryTransformationStrategy._extract_basic_filters(parsed_data)

        # Extraction spécifique contact
        entities = parsed_data.get('entities', [])
        for entity in entities:
            if entity['type'] == 'EMAIL':
                filters['contact_email'] = entity['value']
            elif entity['type'] == 'PERSON':
                filters['contact_name'] = entity['value']

        return {
            'query_type': QueryType.CONTACT,
            'semantic_text': parsed_data.get('semantic_text', ''),
            'filters': filters,
            'similarity_threshold': SIMILARITY_THRESHOLDS[QueryType.CONTACT],
            'limit': QUERY_LIMITS[QueryType.CONTACT],
            'include_snippets': True
        }

    @staticmethod
    def transform_temporal(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transformation pour recherche temporelle"""
        filters = QueryTransformationStrategy._extract_basic_filters(parsed_data)

        # Extraction dates spécifiques
        entities = parsed_data.get('entities', [])
        for entity in entities:
            if entity['type'] == 'TEMPORAL':
                date_value = entity['value']
                if QueryTransformationStrategy._is_valid_date(date_value):
                    filters['date_from'] = date_value
                    # Si date spécifique, chercher toute la journée
                    if len(date_value) == 10:  # Format YYYY-MM-DD
                        filters['date_to'] = date_value

        return {
            'query_type': QueryType.TIME_RANGE,
            'semantic_text': parsed_data.get('semantic_text', ''),
            'filters': filters,
            'similarity_threshold': SIMILARITY_THRESHOLDS[QueryType.TIME_RANGE],
            'limit': QUERY_LIMITS[QueryType.TIME_RANGE],
            'include_snippets': True
        }

    @staticmethod
    def transform_topic(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transformation pour recherche par topic"""
        filters = QueryTransformationStrategy._extract_basic_filters(parsed_data)

        # Extraction topics
        entities = parsed_data.get('entities', [])
        topic_ids = []
        for entity in entities:
            if entity['type'] == 'TOPIC':
                topic_ids.append(entity['value'])

        if topic_ids:
            filters['topic_ids'] = topic_ids

        return {
            'query_type': QueryType.TOPIC,
            'semantic_text': parsed_data.get('semantic_text', ''),
            'filters': filters,
            'similarity_threshold': SIMILARITY_THRESHOLDS[QueryType.TOPIC],
            'limit': QUERY_LIMITS[QueryType.TOPIC],
            'include_snippets': True
        }

    @staticmethod
    def transform_thread(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transformation pour recherche dans threads"""
        return {
            'query_type': QueryType.THREAD,
            'semantic_text': parsed_data.get('semantic_text', ''),
            'filters': QueryTransformationStrategy._extract_basic_filters(parsed_data),
            'similarity_threshold': SIMILARITY_THRESHOLDS[QueryType.THREAD],
            'limit': QUERY_LIMITS[QueryType.THREAD],
            'include_snippets': True
        }

    @staticmethod
    def transform_combined(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transformation pour requête combinée complexe"""
        filters = QueryTransformationStrategy._extract_basic_filters(parsed_data)

        # Intégrer toutes les entités pertinentes
        entities = parsed_data.get('entities', [])
        contact_found = False
        temporal_found = False

        for entity in entities:
            if entity['type'] == 'EMAIL' and not contact_found:
                filters['contact_email'] = entity['value']
                contact_found = True
            elif entity['type'] == 'PERSON' and not contact_found:
                filters['contact_name'] = entity['value']
                contact_found = True
            elif entity['type'] == 'TEMPORAL' and not temporal_found:
                if QueryTransformationStrategy._is_valid_date(entity['value']):
                    filters['date_from'] = entity['value']
                    temporal_found = True
            elif entity['type'] == 'TOPIC':
                if 'topic_ids' not in filters:
                    filters['topic_ids'] = []
                filters['topic_ids'].append(entity['value'])

        return {
            'query_type': QueryType.COMBINED,
            'semantic_text': parsed_data.get('semantic_text', ''),
            'filters': filters,
            'similarity_threshold': SIMILARITY_THRESHOLDS[QueryType.COMBINED],
            'limit': QUERY_LIMITS[QueryType.COMBINED],
            'include_snippets': True
        }

    @staticmethod
    def _extract_basic_filters(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extrait les filtres de base depuis les données parsées"""
        return parsed_data.get('filters', {})

    @staticmethod
    def _is_valid_date(date_str: str) -> bool:
        """Vérifie si une chaîne est une date valide"""
        from datetime import datetime
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False


class SemanticQueryTransformer:
    """
    Transformateur principal utilisant uniquement spaCy et les patterns.
    """

    def __init__(self):
        self.parser = NLPParsingService()
        self.validator = QueryValidationService()
        self.transformer_service = TransformationService()

        # Mapping des intentions vers transformations
        self.transformation_strategies = {
            IntentType.SEARCH_SEMANTIC: QueryTransformationStrategy.transform_semantic,
            IntentType.SEARCH_CONTACT: QueryTransformationStrategy.transform_contact,
            IntentType.SEARCH_TEMPORAL: QueryTransformationStrategy.transform_temporal,
            IntentType.SEARCH_TOPIC: QueryTransformationStrategy.transform_topic,
            IntentType.SEARCH_THREAD: QueryTransformationStrategy.transform_thread,
            IntentType.SEARCH_ATTACHMENT: QueryTransformationStrategy.transform_semantic,  # Fallback
            IntentType.SEARCH_COMBINED: QueryTransformationStrategy.transform_combined,
            IntentType.UNKNOWN: QueryTransformationStrategy.transform_semantic
        }

    def transform_query(self, request) -> Dict[str, Any]:
        """
        Transforme une requête naturelle en structure sémantique

        Args:
            request: Requête en langage naturel avec contexte

        Returns:
            dict: Structure sémantique complète pour la recherche
        """
        start_time = time.time()

        # Valider la requête d'entrée
        is_valid, errors = self.validator.validate_input_query(request.query)
        if not is_valid:
            return self._create_error_response("Requête invalide", errors, start_time)

        # Parser avec spaCy et patterns
        try:
            parsed_result = self.parser.parse_query(request.query, request.user_context)
        except Exception as e:
            return self._create_error_response(f"Erreur de parsing: {str(e)}", [], start_time)

        # Valider le résultat du parsing
        is_valid, errors = self.validator.validate_parsing_result(parsed_result)
        if not is_valid:
            return self._create_error_response("Résultat de parsing invalide", errors, start_time)

        # Transformation en structure sémantique
        semantic_query = self._apply_transformation_strategy(parsed_result)

        # Validation et nettoyage final
        validated_query = self._validate_and_clean(semantic_query)

        # Ajout des métadonnées
        transformation_time = (time.time() - start_time) * 1000

        return {
            'success': True,
            'semantic_query': validated_query,
            'processing_info': {
                'transformation_time_ms': transformation_time,
                'parsing_method': 'spacy_patterns',
                'confidence': parsed_result.get('confidence', 0.5),
                'original_intent': parsed_result.get('intent', 'unknown'),
                'language_detected': parsed_result.get('language', 'auto')
            },
            'debug_info': {
                'parsed_entities': parsed_result.get('entities', []),
                'extracted_filters': parsed_result.get('filters', {}),
                'semantic_text': parsed_result.get('semantic_text', '')
            }
        }

    def _apply_transformation_strategy(self, parsed_result: Dict[str, Any]) -> Dict[str, Any]:
        """Applique la stratégie de transformation selon l'intention"""
        intent_str = parsed_result.get('intent', IntentType.SEARCH_SEMANTIC.value)

        # Mapper string vers enum
        try:
            intent = IntentType(intent_str)
        except ValueError:
            intent = IntentType.SEARCH_SEMANTIC

        # Appliquer stratégie correspondante
        strategy = self.transformation_strategies.get(
            intent,
            QueryTransformationStrategy.transform_semantic
        )

        return strategy(parsed_result)

    def _validate_and_clean(self, semantic_query: Dict[str, Any]) -> Dict[str, Any]:
        """Valide et nettoie la structure sémantique finale"""
        # Appliquer les valeurs par défaut
        cleaned_query = DEFAULT_FILTERS.copy()
        cleaned_query.update(semantic_query)

        # Validation des types requis
        if 'query_type' not in cleaned_query:
            cleaned_query['query_type'] = QueryType.SEMANTIC.value

        if 'semantic_text' not in cleaned_query:
            cleaned_query['semantic_text'] = ''

        if 'filters' not in cleaned_query:
            cleaned_query['filters'] = {}

        # Validation des limites
        cleaned_query['limit'] = self.transformer_service.validate_and_format_limit(
            cleaned_query.get('limit', DEFAULT_FILTERS['limit'])
        )

        # Validation du seuil de similarité
        threshold = cleaned_query.get('similarity_threshold', DEFAULT_FILTERS['similarity_threshold'])
        cleaned_query['similarity_threshold'] = max(0.1, min(1.0, threshold))

        # Nettoyage du texte sémantique
        semantic_text = cleaned_query.get('semantic_text', '').strip()
        if len(semantic_text) < 2:
            cleaned_query['semantic_text'] = 'recherche'

        # Validation des filtres
        filters = cleaned_query.get('filters', {})
        cleaned_query['filters'] = self._clean_filters(filters)

        return cleaned_query

    def _clean_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Nettoie les filtres"""
        cleaned = {}

        # Filtres de date
        for date_field in ['date_from', 'date_to']:
            if date_field in filters and self._is_valid_date_format(filters[date_field]):
                cleaned[date_field] = filters[date_field]

        # Filtres de contact
        if 'contact_email' in filters and filters['contact_email']:
            cleaned['contact_email'] = filters['contact_email']

        if 'contact_name' in filters and filters['contact_name']:
            cleaned['contact_name'] = self.transformer_service.normalize_person_name(filters['contact_name'])

        # Filtres booléens
        bool_fields = ['has_attachments', 'is_unread', 'is_important']
        for field in bool_fields:
            if field in filters and isinstance(filters[field], bool):
                cleaned[field] = filters[field]

        # Filtres de liste
        if 'topic_ids' in filters and isinstance(filters['topic_ids'], list):
            cleaned['topic_ids'] = [str(topic) for topic in filters['topic_ids'] if topic]

        return cleaned

    def _is_valid_date_format(self, date_str: str) -> bool:
        """Vérifie le format de date YYYY-MM-DD"""
        from datetime import datetime
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except (ValueError, TypeError):
            return False

    def _create_error_response(self, message: str, errors: list, start_time: float) -> Dict[str, Any]:
        """Crée une réponse d'erreur standardisée"""
        return {
            'success': False,
            'error': {
                'message': message,
                'details': errors,
                'type': 'validation_error'
            },
            'processing_info': {
                'transformation_time_ms': (time.time() - start_time) * 1000,
                'parsing_method': 'spacy_patterns',
                'confidence': 0.0
            }
        }


# Instance singleton
_transformer_instance = None


def get_query_transformer():
    """Récupère l'instance singleton du transformer"""
    global _transformer_instance
    if _transformer_instance is None:
        _transformer_instance = SemanticQueryTransformer()
    return _transformer_instance