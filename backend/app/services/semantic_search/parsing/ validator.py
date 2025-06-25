"""
Validateur d'entités pour les requêtes en langage naturel.

"""

import re
from datetime import datetime
from typing import List
from .types import ParsedEntity
from .base_parser import is_valid_email
from backend.app.services.semantic_search.patterns import is_blacklisted_name


class EntityValidator:
    """
    Validateur d'entités
    """

    def _validate_entities(self, entities: List[ParsedEntity], language: str) -> List[ParsedEntity]:
        """Valide et filtre les entités extraites - Code original inchangé"""
        validated_entities = []

        for entity in entities:
            is_valid = True

            # Validation spécifique par type
            if entity.type == 'PERSON':
                is_valid = self._is_valid_person_name(entity.value, language)
            elif entity.type == 'EMAIL':
                is_valid = self._is_valid_email(entity.value)
            elif entity.type == 'TEMPORAL':
                # Vérifier que la date est raisonnable
                try:
                    datetime.strptime(entity.value, '%Y-%m-%d')
                except ValueError:
                    is_valid = False

            if is_valid:
                validated_entities.append(entity)

        return validated_entities

    def _is_valid_person_name(self, name: str, language: str) -> bool:
        """Validation  des noms de personnes"""
        if not name or len(name.strip()) < 2:
            return False

        name_clean = name.strip()

        # Vérifier blacklist
        if is_blacklisted_name(name_clean, language):
            return False

        # Noms trop courts (sauf exceptions)
        if len(name_clean) < 3 and name_clean.lower() :
            return False

        # Pattern de nom réaliste
        name_pattern = r"^[A-Z][a-z]+(?:[-'\s][A-Z][a-z]+)*$"
        if not re.match(name_pattern, name_clean):
            return False

        # Rejeter les mots trop génériques
        generic_words = ['user', 'admin', 'client', 'customer', 'support', 'team', 'group', 'équipe']
        if name_clean.lower() in generic_words:
            return False

        return True

    def _is_valid_email(self, email: str) -> bool:
        """Validation d'adresse email"""
        return is_valid_email(email)