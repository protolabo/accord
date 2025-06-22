import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import pytz
import calendar

# Import du nouveau système de patterns
from backend.app.services.semantic_search.patterns import get_patterns, is_blacklisted_name, get_stopwords

# Import conditionnel de spaCy pour NER
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    raise RuntimeError("spaCy n'est pas installé ")


class IntentType(Enum):
    """Types d'intention détectés dans les requêtes"""
    SEARCH_SEMANTIC = "search_semantic"  # Recherche par contenu/sens
    SEARCH_CONTACT = "search_contact"  # Recherche par expéditeur/contact
    SEARCH_TEMPORAL = "search_temporal"  # Recherche temporelle
    SEARCH_TOPIC = "search_topic"  # Recherche par sujet/catégorie
    SEARCH_THREAD = "search_thread"  # Recherche dans conversations
    SEARCH_ATTACHMENT = "search_attachment"  # Recherche avec fichiers joints
    SEARCH_COMBINED = "search_combined"  # Requête combinée
    UNKNOWN = "unknown"


@dataclass
class ParsedEntity:
    """Entité extraite de la requête"""
    type: str  # Type d'entité (PERSON, DATE, EMAIL, etc.)
    value: str  # Valeur normalisée
    original: str  # Texte original
    confidence: float  # Score de confiance


@dataclass
class QueryContext:
    """Contexte de la requête utilisateur"""
    user_email: Optional[str] = None
    timezone: str = "UTC"
    language: str = "fr"
    recent_searches: List[str] = None


class NaturalLanguageQueryParser:
    """
    Parseur principal pour les requêtes en langage naturel.
    Utilise patterns enrichis, analyse heuristique, NER et validation intelligente.
    """

    def __init__(self):
        self.nlp_model = self._load_spacy_model()
        self._load_patterns()

    def _load_spacy_model(self):
        """Charge le modèle spaCy si disponible"""
        if not SPACY_AVAILABLE:
            return None

        try:
            # Essayer le modèle français en premier
            return spacy.load("fr_core_news_sm")
        except OSError:
            try:
                # Fallback sur modèle anglais
                return spacy.load("en_core_web_sm")
            except OSError:
                print("⚠️ Aucun modèle spaCy disponible, utilisation des patterns uniquement")
                return None

    def _load_patterns(self):
        """Charge les patterns enrichis"""
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
        Parse une requête en langage naturel

        Args:
            query: Requête utilisateur
            context: Contexte optionnel

        Returns:
            Dictionnaire avec intention, entités et métadonnées
        """
        if not query or len(query.strip()) < 2:
            return self._empty_parse_result(query)

        # Détecter la langue en premier
        language = self._detect_language(query)

        # Nettoyer la requête
        cleaned_query = self._clean_query(query)

        # Extraire les entités avec patterns adaptés à la langue
        entities = self._extract_entities(cleaned_query, language)

        # Détecter l'intention
        intent = self._detect_intent(cleaned_query, entities, language)

        # Extraire les filtres
        filters = self._extract_filters(cleaned_query, entities, context)

        # Extraire le texte sémantique pur
        semantic_text = self._extract_semantic_text(cleaned_query, entities, language)

        # Calculer la confiance
        confidence = self._calculate_overall_confidence(entities, intent, language)

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

    def _clean_query(self, query: str) -> str:
        """Nettoie et normalise la requête"""
        # Supprimer caractères spéciaux inutiles mais garder @ pour emails
        cleaned = re.sub(r'[^\w\s@.-]', ' ', query)

        # Normaliser les espaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        # Convertir en minuscules pour pattern matching
        return cleaned.lower()

    def _detect_language(self, query: str) -> str:
        """Détection de langue améliorée"""
        query_lower = query.lower()

        # Indicateurs français
        french_indicators = [
            'emails', 'mails', 'messages', 'courriels', 'de', 'du', 'des', 'avec', 'dans',
            'par', 'pour', 'hier', 'aujourd', 'demain', 'semaine', 'mois', 'année',
            'pièce jointe', 'expéditeur', 'destinataire', 'conversation', 'réunion',
            'envoyé', 'envoyés', 'sans', 'entre'
        ]

        # Indicateurs anglais
        english_indicators = [
            'email', 'mail', 'message', 'from', 'to', 'with', 'in', 'by', 'for',
            'yesterday', 'today', 'tomorrow', 'week', 'month', 'year',
            'attachment', 'sender', 'recipient', 'conversation', 'meeting',
            'sent', 'without', 'between'
        ]

        # Compter les occurrences
        french_score = sum(1 for word in french_indicators if word in query_lower)
        english_score = sum(1 for word in english_indicators if word in query_lower)

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

    def _extract_entities(self, query: str, language: str) -> List[ParsedEntity]:
        """Extrait les entités nommées avec patterns enrichis"""
        entities = []

        # 1. Extraction avec spaCy si disponible
        if self.nlp_model:
            entities.extend(self._extract_entities_spacy(query))

        # 2. Extraction avec patterns enrichis
        entities.extend(self._extract_entities_patterns(query, language))

        # 3. Déduplication et validation
        entities = self._deduplicate_entities(entities)
        entities = self._validate_entities(entities, language)

        return entities

    def _extract_entities_spacy(self, query: str) -> List[ParsedEntity]:
        """Extraction d'entités avec spaCy"""
        entities = []

        try:
            doc = self.nlp_model(query)

            for ent in doc.ents:
                # Mapper les labels spaCy vers nos types
                entity_type = self._map_spacy_label(ent.label_)

                if entity_type:
                    entity = ParsedEntity(
                        type=entity_type,
                        value=ent.text.strip(),
                        original=ent.text,
                        confidence=0.8  # Confiance de base pour spaCy
                    )
                    entities.append(entity)

        except Exception as e:
            print(f"⚠️ Erreur spaCy NER: {e}")

        return entities

    def _map_spacy_label(self, label: str) -> Optional[str]:
        """Mappe les labels spaCy vers nos types d'entités"""
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
        """Extraction d'entités avec patterns enrichis"""
        entities = []

        # Sélectionner les patterns selon la langue
        if language == 'auto':
            patterns_data = self.all_patterns
        else:
            patterns_data = self.patterns_fr if language == 'fr' else self.patterns_en

        # Extraction temporelle
        temporal_patterns = patterns_data.get('temporal', {})
        for pattern, config in temporal_patterns.items():
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                try:
                    normalized_value = self._normalize_temporal_entity(match.group(), config)

                    # Gérer les plages de dates qui retournent un dict
                    if isinstance(normalized_value, dict) and 'start' in normalized_value:
                        # Créer deux entités pour la plage
                        entity_start = ParsedEntity(
                            type='TEMPORAL',
                            value=normalized_value['start'],
                            original=match.group(),
                            confidence=0.9
                        )
                        entity_end = ParsedEntity(
                            type='TEMPORAL',
                            value=normalized_value['end'],
                            original=match.group(),
                            confidence=0.9
                        )
                        entities.extend([entity_start, entity_end])
                    else:
                        entity = ParsedEntity(
                            type='TEMPORAL',
                            value=normalized_value,
                            original=match.group(),
                            confidence=0.9
                        )
                        entities.append(entity)
                except Exception as e:
                    print(f"⚠️ Erreur normalisation temporelle: {e}")

        # Extraction de contacts
        contact_patterns = patterns_data.get('contact', {})
        for pattern, contact_type in contact_patterns.items():
            if contact_type in ['from_contact', 'to_contact', 'team_contact']:
                matches = re.finditer(pattern, query, re.IGNORECASE)
                for match in matches:
                    try:
                        # Le nom est généralement le dernier groupe capturé
                        name = match.groups()[-1].strip() if match.groups() else match.group().strip()

                        # Nettoyer le nom
                        name = re.sub(r'^(de|from|par|by|à|to|pour|for)\s+', '', name, flags=re.IGNORECASE)

                        # Validation du nom
                        if self._is_valid_person_name(name, language):
                            entity = ParsedEntity(
                                type='PERSON',
                                value=name.title(),
                                original=match.group(),
                                confidence=0.7
                            )
                            entities.append(entity)

                            # Ajouter un marqueur pour le type de contact
                            if contact_type == 'to_contact':
                                entity = ParsedEntity(
                                    type='RECIPIENT_MARKER',
                                    value='recipient',
                                    original=match.group(),
                                    confidence=0.9
                                )
                                entities.append(entity)
                    except Exception as e:
                        print(f"⚠️ Erreur extraction contact: {e}")

            elif contact_type == 'email_address':
                matches = re.finditer(pattern, query, re.IGNORECASE)
                for match in matches:
                    email = match.group().strip().lower()
                    if self._is_valid_email(email):
                        entity = ParsedEntity(
                            type='EMAIL',
                            value=email,
                            original=match.group(),
                            confidence=0.95
                        )
                        entities.append(entity)

        # Extraction de topics
        topic_patterns = patterns_data.get('topic', {})
        for pattern, topic_type in topic_patterns.items():
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                entity = ParsedEntity(
                    type='TOPIC',
                    value=topic_type,
                    original=match.group(),
                    confidence=0.8
                )
                entities.append(entity)

        return entities

    def _is_valid_person_name(self, name: str, language: str) -> bool:
        """Validation intelligente des noms de personnes"""
        if not name or len(name.strip()) < 2:
            return False

        name_clean = name.strip()

        # Vérifier blacklist
        if is_blacklisted_name(name_clean, language):
            return False

        # Noms trop courts (sauf exceptions)
        if len(name_clean) < 3 and name_clean.lower() not in ['jo', 'li', 'xu']:
            return False

        # Pattern de nom réaliste
        # Accepter: "Marie", "Jean Dupont", "Marie-Claire", "O'Connor"
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
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))

    def _normalize_temporal_entity(self, text: str, config: Dict[str, Any], timezone: str = "UTC") -> str:
        """Normalise une entité temporelle en date ISO avec support timezone et plages"""
        try:
            # Utiliser timezone pour calculs
            tz = pytz.timezone(timezone) if timezone != "UTC" else pytz.UTC
            now = datetime.now(tz)

            if config['type'] == 'relative_day':
                target_date = now + timedelta(days=config['offset'])
                return target_date.strftime('%Y-%m-%d')

            elif config['type'] == 'relative_week':
                # Début de semaine + offset
                days_since_monday = now.weekday()
                week_start = now - timedelta(days=days_since_monday)
                target_date = week_start + timedelta(weeks=config['offset'])
                return target_date.strftime('%Y-%m-%d')

            elif config['type'] == 'relative_month':
                # Calcul approximatif par mois
                if config['offset'] == -1:  # Mois dernier
                    if now.month == 1:
                        target_date = now.replace(year=now.year - 1, month=12, day=1)
                    else:
                        target_date = now.replace(month=now.month - 1, day=1)
                elif config['offset'] == 0:  # Ce mois
                    target_date = now.replace(day=1)
                else:  # Mois suivant
                    if now.month == 12:
                        target_date = now.replace(year=now.year + 1, month=1, day=1)
                    else:
                        target_date = now.replace(month=now.month + 1, day=1)
                return target_date.strftime('%Y-%m-%d')

            elif config['type'] == 'relative_year':
                target_date = now.replace(year=now.year + config['offset'], month=1, day=1)
                return target_date.strftime('%Y-%m-%d')

            elif config['type'] == 'absolute_date_fr':
                # Format DD/MM/YYYY ou DD-MM-YYYY
                date_match = re.match(r'(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})', text)
                if date_match:
                    day, month, year = date_match.groups()
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

            elif config['type'] == 'absolute_date_us':
                # Format MM/DD/YYYY
                date_match = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', text)
                if date_match:
                    month, day, year = date_match.groups()
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

            elif config['type'] == 'iso_date':
                return text  # Déjà au bon format

            elif config['type'] == 'weekday':
                # Calculer le prochain/dernier jour de la semaine
                target_weekday = config['day']
                days_ahead = target_weekday - now.weekday()
                if days_ahead <= 0:  # Si c'est aujourd'hui ou dans le passé
                    days_ahead += 7
                target_date = now + timedelta(days=days_ahead)
                return target_date.strftime('%Y-%m-%d')

            elif config['type'] == 'month':
                # Mois spécifique dans l'année courante
                target_month = config['month']
                target_date = now.replace(month=target_month, day=1)
                return target_date.strftime('%Y-%m-%d')

            elif config['type'] == 'date_range_month':
                # Plage de dates dans un mois
                if 'capture_groups' in config:
                    match = re.search(
                        r'(?:entre\s+le\s+|du\s+)?(\d{1,2})\s+(?:et|au|jusqu\'au)\s+(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)',
                        text, re.IGNORECASE
                    )
                    if match:
                        start_day, end_day, month = match.groups()
                        month_num = self._get_month_number(month)
                        year = now.year
                        return {
                            'start': f"{year}-{month_num:02d}-{int(start_day):02d}",
                            'end': f"{year}-{month_num:02d}-{int(end_day):02d}"
                        }

            elif config['type'] == 'date_range_iso':
                # Plage de dates ISO
                match = re.search(r'(\d{4}-\d{2}-\d{2})\s+(?:et|au|jusqu\'au|to|until)\s+(\d{4}-\d{2}-\d{2})', text)
                if match:
                    return {
                        'start': match.group(1),
                        'end': match.group(2)
                    }

            elif config['type'] == 'month_period':
                # Début/milieu/fin de mois
                match = re.search(
                    r'(début|milieu|fin)\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)',
                    text, re.IGNORECASE
                )
                if match:
                    period, month_name = match.groups()
                    month_num = self._get_month_number(month_name)
                    year = now.year

                    if period == 'début':
                        return f"{year}-{month_num:02d}-01"
                    elif period == 'milieu':
                        return f"{year}-{month_num:02d}-15"
                    elif period == 'fin':
                        last_day = calendar.monthrange(year, month_num)[1]
                        return f"{year}-{month_num:02d}-{last_day}"

        except Exception as e:
            print(f"⚠️ Erreur normalisation temporelle: {e}")

        # Fallback: retourner le texte original
        return text

    def _get_month_number(self, month_name: str) -> int:
        """Convertit un nom de mois en numéro"""
        months_fr = {
            'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4,
            'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8,
            'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12
        }
        months_en = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }

        month_lower = month_name.lower()
        return months_fr.get(month_lower, months_en.get(month_lower, 1))

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

    def _validate_entities(self, entities: List[ParsedEntity], language: str) -> List[ParsedEntity]:
        """Valide et filtre les entités extraites"""
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

    def _deduplicate_entities(self, entities: List[ParsedEntity]) -> List[ParsedEntity]:
        """Supprime les entités dupliquées en gardant celle avec le meilleur score"""

        # Grouper par valeur normalisée et type
        entity_groups = {}
        for entity in entities:
            key = f"{entity.type}:{entity.value.lower()}"
            if key not in entity_groups:
                entity_groups[key] = []
            entity_groups[key].append(entity)

        # Garder la meilleure entité de chaque groupe
        unique_entities = []
        for group in entity_groups.values():
            # Prendre celle avec la meilleure confiance
            best_entity = max(group, key=lambda e: e.confidence)
            unique_entities.append(best_entity)

        return unique_entities

    def _calculate_overall_confidence(self, entities: List[ParsedEntity], intent: IntentType, language: str) -> float:
        """Calcule un score de confiance global amélioré"""

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