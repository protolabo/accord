"""
Service de validation pour les requêtes et résultats de parsing.
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional

from ..config import PARSING_CONFIG, TEMPORAL_CONFIG


class QueryValidationService:
    """Service pour la validation des requêtes et des résultats de parsing"""

    def __init__(self):
        self.validation_errors = []

    def validate_input_query(self, query: str) -> tuple[bool, List[str]]:
        """
        Valide une requête d'entrée

        Args:
            query (str): Requête à valider

        Returns:
            tuple: (is_valid, list_of_errors)
        """
        self.validation_errors = []

        # Vérifier que la requête n'est pas vide
        if not query or not isinstance(query, str):
            self.validation_errors.append("La requête ne peut pas être vide")
            return False, self.validation_errors

        # Vérifier la longueur
        query_length = len(query.strip())
        if query_length < PARSING_CONFIG['min_query_length']:
            self.validation_errors.append(
                f"La requête doit contenir au moins {PARSING_CONFIG['min_query_length']} caractères")

        if query_length > PARSING_CONFIG['max_query_length']:
            self.validation_errors.append(
                f"La requête ne peut pas dépasser {PARSING_CONFIG['max_query_length']} caractères")

        return len(self.validation_errors) == 0, self.validation_errors

    def validate_parsing_result(self, result: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Valide le résultat du parsing

        Args:
            result (dict): Résultat du parsing à valider

        Returns:
            tuple: (is_valid, list_of_errors)
        """
        self.validation_errors = []

        # Vérifier la structure de base
        required_fields = ['intent', 'semantic_text', 'entities', 'filters', 'confidence']
        for field in required_fields:
            if field not in result:
                self.validation_errors.append(f"Champ manquant: {field}")

        # Valider l'intention
        if 'intent' in result:
            if not self._is_valid_intent(result['intent']):
                self.validation_errors.append(f"Intention invalide: {result['intent']}")

        # Valider les entités
        if 'entities' in result:
            entity_errors = self._validate_entities(result['entities'])
            self.validation_errors.extend(entity_errors)

        # Valider les filtres
        if 'filters' in result:
            filter_errors = self._validate_filters(result['filters'])
            self.validation_errors.extend(filter_errors)

        # Valider la confiance
        if 'confidence' in result:
            if not self._is_valid_confidence(result['confidence']):
                self.validation_errors.append("Score de confiance invalide (doit être entre 0 et 1)")

        return len(self.validation_errors) == 0, self.validation_errors

    def validate_semantic_query(self, semantic_query: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Valide une requête sémantique finale

        Args:
            semantic_query (dict): Requête sémantique à valider

        Returns:
            tuple: (is_valid, list_of_errors)
        """
        self.validation_errors = []

        # Vérifier les champs requis
        required_fields = ['query_type', 'filters']
        for field in required_fields:
            if field not in semantic_query:
                self.validation_errors.append(f"Champ requis manquant: {field}")

        # Valider le type de requête
        if 'query_type' in semantic_query:
            from ..config import QueryType
            valid_types = [qt.value for qt in QueryType]
            if semantic_query['query_type'] not in valid_types:
                self.validation_errors.append(f"Type de requête invalide: {semantic_query['query_type']}")

        # Valider la limite
        if 'limit' in semantic_query:
            limit = semantic_query['limit']
            if not isinstance(limit, int) or limit < 1 or limit > PARSING_CONFIG['max_limit']:
                self.validation_errors.append(f"Limite invalide (doit être entre 1 et {PARSING_CONFIG['max_limit']})")

        # Valider le seuil de similarité
        if 'similarity_threshold' in semantic_query:
            threshold = semantic_query['similarity_threshold']
            if not isinstance(threshold, (int, float)) or threshold < 0.1 or threshold > 1.0:
                self.validation_errors.append("Seuil de similarité invalide (doit être entre 0.1 et 1.0)")

        return len(self.validation_errors) == 0, self.validation_errors


    def _is_valid_intent(self, intent: str) -> bool:
        """Valide une intention"""
        from ..config import IntentType
        valid_intents = [it.value for it in IntentType]
        return intent in valid_intents

    def _validate_entities(self, entities: List[Dict[str, Any]]) -> List[str]:
        """Valide la liste des entités"""
        errors = []

        if not isinstance(entities, list):
            errors.append("Les entités doivent être une liste")
            return errors

        valid_entity_types = ['PERSON', 'EMAIL', 'TEMPORAL', 'TOPIC', 'ORGANIZATION', 'LOCATION']

        for i, entity in enumerate(entities):
            if not isinstance(entity, dict):
                errors.append(f"Entité {i}: doit être un dictionnaire")
                continue

            # Vérifier les champs requis
            required_fields = ['type', 'value', 'original', 'confidence']
            for field in required_fields:
                if field not in entity:
                    errors.append(f"Entité {i}: champ manquant '{field}'")

            # Valider le type
            if 'type' in entity and entity['type'] not in valid_entity_types:
                errors.append(f"Entité {i}: type invalide '{entity['type']}'")

            # Valider la confiance
            if 'confidence' in entity:
                if not self._is_valid_confidence(entity['confidence']):
                    errors.append(f"Entité {i}: confiance invalide")

            # Validations spécifiques par type
            if entity.get('type') == 'EMAIL':
                if not self._is_valid_email_entity(entity.get('value', '')):
                    errors.append(f"Entité {i}: email invalide")

            elif entity.get('type') == 'TEMPORAL':
                if not self._is_valid_temporal_entity(entity.get('value', '')):
                    errors.append(f"Entité {i}: date invalide")

        return errors

    def _validate_filters(self, filters: Dict[str, Any]) -> List[str]:
        """Valide les filtres"""
        errors = []

        if not isinstance(filters, dict):
            errors.append("Les filtres doivent être un dictionnaire")
            return errors

        # Valider les emails de contact
        if 'contact_email' in filters:
            if not self._is_valid_email_entity(filters['contact_email']):
                errors.append("Email de contact invalide")

        # Valider les dates
        for date_field in ['date_from', 'date_to']:
            if date_field in filters:
                if not self._is_valid_temporal_entity(filters[date_field]):
                    errors.append(f"Date invalide: {date_field}")

        # Valider les booléens
        bool_fields = ['has_attachments', 'is_unread', 'is_important']
        for field in bool_fields:
            if field in filters and not isinstance(filters[field], bool):
                errors.append(f"Le champ {field} doit être un booléen")

        # Valider les listes
        list_fields = ['topic_ids', 'labels']
        for field in list_fields:
            if field in filters:
                if not isinstance(filters[field], list):
                    errors.append(f"Le champ {field} doit être une liste")
                elif len(filters[field]) > 10:  # Limite raisonnable
                    errors.append(f"Le champ {field} ne peut pas contenir plus de 10 éléments")

        return errors

    def _is_valid_confidence(self, confidence: Any) -> bool:
        """Valide un score de confiance"""
        return (isinstance(confidence, (int, float)) and
                0.0 <= confidence <= 1.0)

    def _is_valid_email_entity(self, email: str) -> bool:
        """Valide une entité email"""
        if not isinstance(email, str):
            return False

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))

    def _is_valid_temporal_entity(self, date_str: str) -> bool:
        """Valide une entité temporelle"""
        if not isinstance(date_str, str):
            return False

        # Essayer de parser avec les formats supportés
        for date_format in TEMPORAL_CONFIG['date_formats']:
            try:
                datetime.strptime(date_str, date_format)
                return True
            except ValueError:
                continue

        # Essayer le format ISO
        try:
            datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return True
        except ValueError:
            return False

    def get_last_errors(self) -> List[str]:
        """Retourne les dernières erreurs de validation"""
        return self.validation_errors.copy()