"""
Service de parsing NLP utilisant spaCy et les patterns enrichis.
"""

import re
import spacy
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..core.patterns import get_patterns, is_blacklisted_name, get_stopwords
from ..config import SPACY_CONFIG, CONFIDENCE_WEIGHTS, IntentType


@dataclass
class ParsedEntity:
    """Entité extraite de la requête"""
    type: str
    value: str
    original: str
    confidence: float


class NLPParsingService:
    """Service de parsing NLP avec spaCy et patterns"""

    def __init__(self):
        self.nlp_model = self._load_spacy_model()
        self._load_patterns()

    def _load_spacy_model(self):
        """Charge le modèle spaCy avec fallback"""
        for model_name in SPACY_CONFIG['models_priority']:
            try:
                return spacy.load(model_name)
            except OSError:
                continue

        if SPACY_CONFIG['fallback_enabled']:
            print("⚠️ Aucun modèle spaCy disponible, utilisation des patterns uniquement")
            return None
        else:
            raise RuntimeError("Aucun modèle spaCy disponible")

    def _load_patterns(self):
        """Charge les patterns enrichis"""
        self.all_patterns = get_patterns('auto', 'all')
        self.patterns_fr = get_patterns('fr', 'all')
        self.patterns_en = get_patterns('en', 'all')
        self.stopwords_auto = get_stopwords('auto')

    def parse_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Parse une requête en langage naturel

        Args:
            query (str): Requête utilisateur
            context (dict): Contexte optionnel

        Returns:
            dict: Résultat du parsing avec entités et intention
        """
        if not query or len(query.strip()) < 2:
            return self._empty_parse_result(query)

        # Détecter la langue
        language = self._detect_language(query)

        # Nettoyer la requête
        cleaned_query = self._clean_query(query)

        # Extraire les entités
        entities = self._extract_entities(cleaned_query, language)

        # Détecter l'intention
        intent = self._detect_intent(cleaned_query, entities, language)

        # Extraire les filtres
        filters = self._extract_filters(cleaned_query, entities, context)

        # Extraire le texte sémantique
        semantic_text = self._extract_semantic_text(cleaned_query, entities, language)

        # Calculer la confiance
        confidence = self._calculate_confidence(entities, intent, language)

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
                'parsing_method': 'spacy_patterns'
            }
        }

    def _detect_language(self, query: str) -> str:
        """Détection de langue optimisée"""
        query_lower = query.lower()

        # Indicateurs français
        french_indicators = [
            'emails', 'mails', 'messages', 'courriels', 'de', 'du', 'des', 'avec',
            'hier', 'aujourd', 'semaine', 'mois', 'pièce jointe', 'expéditeur'
        ]

        # Indicateurs anglais
        english_indicators = [
            'email', 'mail', 'message', 'from', 'to', 'with', 'yesterday',
            'today', 'week', 'month', 'attachment', 'sender'
        ]

        french_score = sum(1 for word in french_indicators if word in query_lower)
        english_score = sum(1 for word in english_indicators if word in query_lower)

        if french_score > english_score:
            return 'fr'
        elif english_score > french_score:
            return 'en'
        else:
            return 'auto'

    def _clean_query(self, query: str) -> str:
        """Nettoie et normalise la requête"""
        cleaned = re.sub(r'[^\w\s@.-]', ' ', query)
        return re.sub(r'\s+', ' ', cleaned).strip().lower()

    def _extract_entities(self, query: str, language: str) -> List[ParsedEntity]:
        """Extrait les entités avec spaCy et patterns"""
        entities = []

        # Extraction avec spaCy si disponible
        if self.nlp_model:
            entities.extend(self._extract_entities_spacy(query))

        # Extraction avec patterns (toujours)
        entities.extend(self._extract_entities_patterns(query, language))

        # Déduplication et validation
        entities = self._deduplicate_entities(entities)
        entities = self._validate_entities(entities, language)

        return entities

    def _extract_entities_spacy(self, query: str) -> List[ParsedEntity]:
        """Extraction avec spaCy"""
        entities = []

        try:
            doc = self.nlp_model(query)
            for ent in doc.ents:
                entity_type = self._map_spacy_label(ent.label_)
                if entity_type:
                    entity = ParsedEntity(
                        type=entity_type,
                        value=ent.text.strip(),
                        original=ent.text,
                        confidence=CONFIDENCE_WEIGHTS['spacy_entity']
                    )
                    entities.append(entity)
        except Exception as e:
            print(f"⚠️ Erreur spaCy NER: {e}")

        return entities

    def _map_spacy_label(self, label: str) -> Optional[str]:
        """Mappe les labels spaCy vers nos types"""
        mapping = {
            'PERSON': 'PERSON',
            'PER': 'PERSON',
            'DATE': 'TEMPORAL',
            'TIME': 'TEMPORAL',
            'ORG': 'ORGANIZATION',
            'LOC': 'LOCATION',
            'MISC': 'MISC'
        }
        return mapping.get(label)

    def _extract_entities_patterns(self, query: str, language: str) -> List[ParsedEntity]:
        """Extraction avec patterns enrichis"""
        entities = []

        # Sélectionner les patterns selon la langue
        patterns_data = self._get_patterns_for_language(language)

        # Extraction temporelle
        entities.extend(self._extract_temporal_entities(query, patterns_data))

        # Extraction de contacts
        entities.extend(self._extract_contact_entities(query, patterns_data))

        # Extraction de topics
        entities.extend(self._extract_topic_entities(query, patterns_data))

        return entities

    def _get_patterns_for_language(self, language: str) -> Dict[str, Any]:
        """Récupère les patterns pour la langue"""
        if language == 'auto':
            return self.all_patterns
        elif language == 'fr':
            return self.patterns_fr
        else:
            return self.patterns_en

    def _extract_temporal_entities(self, query: str, patterns_data: Dict[str, Any]) -> List[ParsedEntity]:
        """Extrait les entités temporelles"""
        entities = []
        temporal_patterns = patterns_data.get('temporal', {})

        for pattern, config in temporal_patterns.items():
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                try:
                    normalized_value = self._normalize_temporal_entity(match.group(), config)
                    entity = ParsedEntity(
                        type='TEMPORAL',
                        value=normalized_value,
                        original=match.group(),
                        confidence=CONFIDENCE_WEIGHTS['pattern_match']
                    )
                    entities.append(entity)
                except Exception:
                    continue

        return entities

    def _extract_contact_entities(self, query: str, patterns_data: Dict[str, Any]) -> List[ParsedEntity]:
        """Extrait les entités de contact"""
        entities = []
        contact_patterns = patterns_data.get('contact', {})

        for pattern, contact_type in contact_patterns.items():
            if contact_type in ['from_contact', 'to_contact']:
                matches = re.finditer(pattern, query, re.IGNORECASE)
                for match in matches:
                    try:
                        name = match.groups()[-1].strip() if match.groups() else match.group().strip()
                        name = re.sub(r'^(de|from|par|by|à|to)\s+', '', name, flags=re.IGNORECASE)

                        if self._is_valid_person_name(name):
                            entity = ParsedEntity(
                                type='PERSON',
                                value=name.title(),
                                original=match.group(),
                                confidence=CONFIDENCE_WEIGHTS['pattern_match'] * 0.8
                            )
                            entities.append(entity)
                    except Exception:
                        continue

            elif contact_type == 'email_address':
                matches = re.finditer(pattern, query, re.IGNORECASE)
                for match in matches:
                    email = match.group().strip().lower()
                    if self._is_valid_email(email):
                        entity = ParsedEntity(
                            type='EMAIL',
                            value=email,
                            original=match.group(),
                            confidence=CONFIDENCE_WEIGHTS['pattern_match']
                        )
                        entities.append(entity)

        return entities

    def _extract_topic_entities(self, query: str, patterns_data: Dict[str, Any]) -> List[ParsedEntity]:
        """Extrait les entités de topic"""
        entities = []
        topic_patterns = patterns_data.get('topic', {})

        for pattern, topic_type in topic_patterns.items():
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                entity = ParsedEntity(
                    type='TOPIC',
                    value=topic_type,
                    original=match.group(),
                    confidence=CONFIDENCE_WEIGHTS['pattern_match'] * 0.9
                )
                entities.append(entity)

        return entities

    def _normalize_temporal_entity(self, text: str, config: Dict[str, Any]) -> str:
        """Normalise une entité temporelle en date ISO"""
        from ..services.transformation_service import normalize_temporal_entity
        return normalize_temporal_entity(text, config)

    def _is_valid_person_name(self, name: str) -> bool:
        """Valide un nom de personne"""
        if not name or len(name.strip()) < 2:
            return False

        name_clean = name.strip()

        if is_blacklisted_name(name_clean):
            return False

        if len(name_clean) < 3 and name_clean.lower() not in ['jo', 'li', 'xu']:
            return False

        name_pattern = r"^[A-Z][a-z]+(?:[-'\s][A-Z][a-z]+)*$"
        return bool(re.match(name_pattern, name_clean))

    def _is_valid_email(self, email: str) -> bool:
        """Valide une adresse email"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))

    def _detect_intent(self, query: str, entities: List[ParsedEntity], language: str) -> IntentType:
        """Détecte l'intention principale"""
        intent_scores = {intent: 0.0 for intent in IntentType}

        # Patterns d'intention
        patterns_data = self._get_patterns_for_language(language)
        intent_patterns = patterns_data.get('intent', {})

        # Scoring basé sur les patterns
        for intent_name, patterns_by_lang in intent_patterns.items():
            if intent_name in ['search_contact', 'search_temporal', 'search_attachment', 'search_thread']:
                intent_enum = getattr(IntentType, intent_name.upper(), IntentType.UNKNOWN)

                patterns_list = patterns_by_lang.get(language, []) if language != 'auto' else []
                if language == 'auto':
                    patterns_list.extend(patterns_by_lang.get('fr', []))
                    patterns_list.extend(patterns_by_lang.get('en', []))

                for pattern in patterns_list:
                    if re.search(pattern, query, re.IGNORECASE):
                        intent_scores[intent_enum] += CONFIDENCE_WEIGHTS['intent_detection']

        # Scoring basé sur les entités
        entity_type_counts = {}
        for entity in entities:
            entity_type_counts[entity.type] = entity_type_counts.get(entity.type, 0) + 1

        for entity_type, count in entity_type_counts.items():
            if entity_type in ['EMAIL', 'PERSON']:
                intent_scores[IntentType.SEARCH_CONTACT] += 0.8 * count
            elif entity_type == 'TEMPORAL':
                intent_scores[IntentType.SEARCH_TEMPORAL] += 0.8 * count
            elif entity_type == 'TOPIC':
                intent_scores[IntentType.SEARCH_TOPIC] += 0.6 * count

        # Détection requête combinée
        unique_entity_types = set(e.type for e in entities)
        if len(unique_entity_types) >= 2:
            intent_scores[IntentType.SEARCH_COMBINED] += 0.5

        # Sélection de l'intention avec le score le plus élevé
        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        return best_intent[0] if best_intent[1] > 0 else IntentType.SEARCH_SEMANTIC

    def _extract_filters(self, query: str, entities: List[ParsedEntity], context: Optional[Dict[str, Any]]) -> Dict[
        str, Any]:
        """Extrait les filtres de la requête"""
        filters = {}

        # Filtres temporels
        temporal_entities = [e for e in entities if e.type == 'TEMPORAL']
        if temporal_entities:
            filters['date_from'] = temporal_entities[0].value

        # Filtres de contact
        email_entities = [e for e in entities if e.type == 'EMAIL']
        person_entities = [e for e in entities if e.type == 'PERSON']

        if email_entities:
            filters['contact_email'] = email_entities[0].value
        elif person_entities:
            filters['contact_name'] = person_entities[0].value

        # Filtres de topic
        topic_entities = [e for e in entities if e.type == 'TOPIC']
        if topic_entities:
            filters['topic_ids'] = [e.value for e in topic_entities]

        # Filtres d'action
        patterns_data = self._get_patterns_for_language('auto')
        action_patterns = patterns_data.get('action', {})

        for pattern, action_type in action_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                if action_type == 'has_attachment':
                    filters['has_attachments'] = True
                elif action_type == 'unread':
                    filters['is_unread'] = True
                elif action_type == 'important':
                    filters['is_important'] = True

        return filters

    def _extract_semantic_text(self, query: str, entities: List[ParsedEntity], language: str) -> str:
        """Extrait le texte sémantique pur"""
        semantic_text = query

        # Supprimer les entités structurées
        for entity in entities:
            if entity.type in ['EMAIL', 'TEMPORAL', 'PERSON', 'TOPIC']:
                pattern = re.escape(entity.original)
                semantic_text = re.sub(pattern, '', semantic_text, flags=re.IGNORECASE)

        # Supprimer les mots-outils
        stopwords = get_stopwords(language)
        for stopword in stopwords:
            pattern = r'\b' + re.escape(stopword) + r'\b'
            semantic_text = re.sub(pattern, '', semantic_text, flags=re.IGNORECASE)

        # Nettoyer les espaces
        semantic_text = re.sub(r'\s+', ' ', semantic_text).strip()

        return semantic_text if len(semantic_text) >= 3 else query

    def _deduplicate_entities(self, entities: List[ParsedEntity]) -> List[ParsedEntity]:
        """Supprime les entités dupliquées"""
        entity_groups = {}
        for entity in entities:
            key = f"{entity.type}:{entity.value.lower()}"
            if key not in entity_groups:
                entity_groups[key] = []
            entity_groups[key].append(entity)

        unique_entities = []
        for group in entity_groups.values():
            best_entity = max(group, key=lambda e: e.confidence)
            unique_entities.append(best_entity)

        return unique_entities

    def _validate_entities(self, entities: List[ParsedEntity], language: str) -> List[ParsedEntity]:
        """Valide et filtre les entités"""
        validated_entities = []

        for entity in entities:
            is_valid = True

            if entity.type == 'PERSON':
                is_valid = self._is_valid_person_name(entity.value)
            elif entity.type == 'EMAIL':
                is_valid = self._is_valid_email(entity.value)
            elif entity.type == 'TEMPORAL':
                try:
                    datetime.fromisoformat(entity.value)
                except ValueError:
                    is_valid = False

            if is_valid:
                validated_entities.append(entity)

        return validated_entities

    def _calculate_confidence(self, entities: List[ParsedEntity], intent: IntentType, language: str) -> float:
        """Calcule un score de confiance global"""
        if not entities:
            return 0.3

        # Moyenne pondérée des confiances
        total_confidence = 0
        total_weight = 0

        for entity in entities:
            weight = CONFIDENCE_WEIGHTS.get('entity_validation', 1.0)

            # Ajuster selon le type
            if entity.type == 'EMAIL':
                weight = 1.2
            elif entity.type == 'PERSON' and is_blacklisted_name(entity.value):
                weight = 0.3

            total_confidence += entity.confidence * weight
            total_weight += weight

        base_confidence = total_confidence / total_weight if total_weight > 0 else 0.3

        # Bonus pour intention spécifique
        intent_bonus = 0.1 if intent != IntentType.UNKNOWN else 0.0

        # Bonus pour diversité
        entity_types = set(e.type for e in entities)
        diversity_bonus = min(0.1, len(entity_types) * 0.05)

        final_confidence = base_confidence + intent_bonus + diversity_bonus
        return max(0.1, min(0.9, final_confidence))

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
                'parsing_method': 'fallback'
            }
        }