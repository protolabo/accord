"""
Transformateur de requêtes pour Accord.
Convertit les résultats du parser en structure sémantique optimisée pour la recherche.
Gère la fusion LLM + heuristiques et la validation des requêtes.
"""

import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from backend.app.services.semantic_search.models import SemanticQuery, SearchFilter, QueryType, NaturalLanguageRequest
from backend.app.services.semantic_search.query_parser import get_query_parser, IntentType
from backend.app.services.semantic_search.llm_engine import get_query_parser as get_llm_parser


class QueryTransformationStrategy:
    """Stratégie de transformation basée sur le type d'intention"""

    @staticmethod
    def transform_semantic(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transformation pour requête sémantique pure"""
        return {
            'query_type': QueryType.SEMANTIC,
            'semantic_text': parsed_data.get('semantic_text', ''),
            'filters': QueryTransformationStrategy._extract_basic_filters(parsed_data),
            'similarity_threshold': 0.4,  # Seuil plus élevé pour sémantique
            'limit': 15
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
            'similarity_threshold': 0.2,  # Plus permissif pour contacts
            'limit': 20
        }

    @staticmethod
    def transform_temporal(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transformation pour recherche temporelle"""
        filters = QueryTransformationStrategy._extract_basic_filters(parsed_data)

        # Extraction dates spécifiques
        entities = parsed_data.get('entities', [])
        for entity in entities:
            if entity['type'] == 'TEMPORAL':
                # Parser la date normalisée
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
            'similarity_threshold': 0.3,
            'limit': 25
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
            'similarity_threshold': 0.35,
            'limit': 20
        }

    @staticmethod
    def transform_thread(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transformation pour recherche dans threads"""
        return {
            'query_type': QueryType.THREAD,
            'semantic_text': parsed_data.get('semantic_text', ''),
            'filters': QueryTransformationStrategy._extract_basic_filters(parsed_data),
            'similarity_threshold': 0.3,
            'limit': 10  # Moins de résultats pour threads
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
            'similarity_threshold': 0.25,  # Plus permissif pour combiné
            'limit': 30
        }

    @staticmethod
    def _extract_basic_filters(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extrait les filtres de base depuis les données parsées"""
        return parsed_data.get('filters', {})

    @staticmethod
    def _is_valid_date(date_str: str) -> bool:
        """Vérifie si une chaîne est une date valide"""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False


class SemanticQueryTransformer:
    """
    Transformateur principal qui orchestre le parsing et la transformation.
    Combine heuristiques NLP et LLM pour maximum de robustesse.
    """

    def __init__(self):
        self.nlp_parser = get_query_parser()
        self.llm_parser = get_llm_parser()

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

    def transform_query(self, request: NaturalLanguageRequest) -> Dict[str, Any]:
        """
        Transforme une requête naturelle en structure sémantique optimisée

        Args:
            request: Requête en langage naturel avec contexte

        Returns:
            Structure sémantique complète pour la recherche
        """
        start_time = time.time()
        # 1. Parse avec heuristiques NLP
        nlp_result = self.nlp_parser.parse_query(request.query)
        #nlp_result = {'confidence':0}

        # 2. Parse avec LLM (si disponible et confiance NLP faible)
        llm_result = None
        use_llm = (
                nlp_result.get('confidence', 0) < 0.8 or
                nlp_result.get('intent') == IntentType.UNKNOWN.value
        )

        if use_llm and self.llm_parser.model:
            print("lancement LLM")
            try:
                llm_result = self.llm_parser.parse_query(
                    request.query,
                    request.user_context or {}
                )
            except Exception as e:
                print(f"⚠️ Erreur LLM, utilisation NLP uniquement: {e}")

        # 3. Fusion intelligente des résultats
        merged_result = self._merge_parsing_results(nlp_result, llm_result)

        # 4. Transformation en structure sémantique
        semantic_query = self._apply_transformation_strategy(merged_result)

        # 5. Validation et nettoyage
        validated_query = self._validate_and_clean(semantic_query)

        # 6. Ajout métadonnées
        transformation_time = (time.time() - start_time) * 1000

        return {
            'success': True,
            'semantic_query': validated_query,
            'processing_info': {
                'transformation_time_ms': transformation_time,
                'parsing_method': self._get_parsing_method_used(nlp_result, llm_result),
                'confidence': merged_result.get('confidence', 0.5),
                'original_intent': merged_result.get('intent', 'unknown')
            },
            'debug_info': {
                'nlp_result': nlp_result,
                'llm_result': llm_result if llm_result else {},
                'merged_entities': merged_result.get('entities', [])
            }
        }

    # Combine intelligemment les résultats NLP (spaCy+regex) et LLM (Mistral)
    def _merge_parsing_results(
            self,
            nlp_result: Dict[str, Any],
            llm_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Fusionne intelligemment les résultats NLP et LLM

        Args:
            nlp_result: Résultat du parser heuristique
            llm_result: Résultat du parser LLM (optionnel)

        Returns:
            Résultat fusionné optimisé
        """

        # Si pas de résultat LLM, utiliser NLP uniquement
        if not llm_result:
            return nlp_result

        # Démarrer avec le résultat NLP comme base
        merged = nlp_result.copy()

        # Comparer les confiances
        nlp_confidence = nlp_result.get('confidence', 0)
        llm_confidence = self._estimate_llm_confidence(llm_result)

        # Si LLM significativement plus confiant, privilégier ses résultats
        if llm_confidence > nlp_confidence + 0.2:
            # Utiliser structure LLM comme base
            merged.update({
                'intent': self._map_llm_to_intent(llm_result.get('query_type', 'semantic')),
                'semantic_text': llm_result.get('semantic_text', nlp_result.get('semantic_text', '')),
                'filters': llm_result.get('filters', {}),
                'confidence': llm_confidence
            })

        # Fusionner les entités (NLP généralement meilleur pour NER)
        nlp_entities = nlp_result.get('entities', [])
        llm_filters = llm_result.get('filters', {}) if llm_result else {}

        # Enrichir avec entités extraites des filtres LLM
        if llm_filters:
            synthetic_entities = self._filters_to_entities(llm_filters)
            all_entities = nlp_entities + synthetic_entities
            merged['entities'] = self._deduplicate_merged_entities(all_entities)

        # Fusionner filtres intelligemment
        merged_filters = nlp_result.get('filters', {}).copy()
        if llm_result:
            llm_filters = llm_result.get('filters', {})
            # LLM peut être meilleur pour dates/contacts structurés
            for key in ['contact_email', 'date_from', 'date_to']:
                if key in llm_filters and llm_filters[key]:
                    merged_filters[key] = llm_filters[key]

        merged['filters'] = merged_filters

        return merged

    def _estimate_llm_confidence(self, llm_result: Dict[str, Any]) -> float:
        """Estime la confiance du résultat LLM"""
        if not llm_result:
            return 0.0

        confidence = 0.5  # Base

        # Bonus si query_type détecté
        if llm_result.get('query_type') and llm_result['query_type'] != 'semantic':
            confidence += 0.2

        # Bonus si filtres extraits
        filters = llm_result.get('filters', {})
        if filters:
            confidence += min(0.3, len(filters) * 0.1)

        # Bonus si modèle utilisé (vs fallback)
        meta = llm_result.get('_meta', {})
        if meta.get('model_used') == 'mistral-7b':
            confidence += 0.1

        return min(1.0, confidence)

    def _map_llm_to_intent(self, llm_query_type: str) -> str:
        """Mappe les types LLM vers les intentions NLP"""
        mapping = {
            'semantic': IntentType.SEARCH_SEMANTIC.value,
            'contact': IntentType.SEARCH_CONTACT.value,
            'time_range': IntentType.SEARCH_TEMPORAL.value,
            'topic': IntentType.SEARCH_TOPIC.value,
            'thread': IntentType.SEARCH_THREAD.value,
            'combined': IntentType.SEARCH_COMBINED.value
        }
        return mapping.get(llm_query_type, IntentType.SEARCH_SEMANTIC.value)

    def _filters_to_entities(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convertit les filtres LLM en entités synthétiques"""
        entities = []

        if filters.get('contact_email'):
            entities.append({
                'type': 'EMAIL',
                'value': filters['contact_email'],
                'original': filters['contact_email'],
                'confidence': 0.8
            })

        if filters.get('date_from'):
            entities.append({
                'type': 'TEMPORAL',
                'value': filters['date_from'],
                'original': filters['date_from'],
                'confidence': 0.7
            })

        if filters.get('topic_ids'):
            for topic in filters['topic_ids']:
                entities.append({
                    'type': 'TOPIC',
                    'value': topic,
                    'original': topic,
                    'confidence': 0.6
                })

        return entities

    def _deduplicate_merged_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Déduplique les entités fusionnées"""
        seen = set()
        unique_entities = []

        for entity in entities:
            key = f"{entity['type']}:{entity['value'].lower()}"
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)

        return unique_entities

    def _apply_transformation_strategy(self, parsed_result: Dict[str, Any]) -> Dict[str, Any]:
        """Transforme les données parsées en structure sémantique finale selon l'intention détectée."""

        intent_str = parsed_result.get('intent', IntentType.SEARCH_SEMANTIC.value) # Ex: "search_contact"

        # Mapper string vers enum
        try:
            intent = IntentType(intent_str)  # → SEARCH_CONTACT
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

        # Validation des types requis
        if 'query_type' not in semantic_query:
            semantic_query['query_type'] = QueryType.SEMANTIC

        if 'semantic_text' not in semantic_query:
            semantic_query['semantic_text'] = ''

        if 'filters' not in semantic_query:
            semantic_query['filters'] = {}

        # Validation des limites
        limit = semantic_query.get('limit', 10)
        semantic_query['limit'] = max(1, min(100, limit))

        # Validation du seuil de similarité
        threshold = semantic_query.get('similarity_threshold', 0.3)
        semantic_query['similarity_threshold'] = max(0.1, min(1.0, threshold))

        # Nettoyage du texte sémantique
        semantic_text = semantic_query.get('semantic_text', '').strip()
        if len(semantic_text) < 2:
            # Si texte trop court, utiliser un fallback
            semantic_query['semantic_text'] = 'recherche'

        # Validation des filtres de date
        filters = semantic_query.get('filters', {})
        if 'date_from' in filters:
            if not self._is_valid_date_format(filters['date_from']):
                del filters['date_from']

        if 'date_to' in filters:
            if not self._is_valid_date_format(filters['date_to']):
                del filters['date_to']

        # Nettoyage des filtres vides
        semantic_query['filters'] = {k: v for k, v in filters.items() if v}

        return semantic_query

    def _is_valid_date_format(self, date_str: str) -> bool:
        """Vérifie le format de date YYYY-MM-DD"""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except (ValueError, TypeError):
            return False

    def _get_parsing_method_used(
            self,
            nlp_result: Dict[str, Any],
            llm_result: Optional[Dict[str, Any]]
    ) -> str:
        """Détermine quelle méthode de parsing a été principalement utilisée"""

        if not llm_result:
            return 'nlp_only'

        nlp_confidence = nlp_result.get('confidence', 0)
        llm_confidence = self._estimate_llm_confidence(llm_result)

        if llm_confidence > nlp_confidence + 0.2:
            return 'llm_primary'
        elif abs(llm_confidence - nlp_confidence) < 0.2:
            return 'hybrid_balanced'
        else:
            return 'nlp_primary'


# Instance singleton
_transformer_instance: Optional[SemanticQueryTransformer] = None


def get_query_transformer() -> SemanticQueryTransformer:
    """Récupère l'instance singleton du transformer"""
    global _transformer_instance
    if _transformer_instance is None:
        _transformer_instance = SemanticQueryTransformer()
    return _transformer_instance