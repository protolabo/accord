"""
Extracteur d'entités pour les requêtes en langage naturel.

"""

import re
from typing import List, Optional
from .types import ParsedEntity
from .base_parser import (
    SPACY_AVAILABLE,
    SPACY_LABEL_MAPPING,
    load_spacy_model,
    is_valid_email
)
from backend.app.services.semantic_search.patterns import get_patterns, is_blacklisted_name


class EntityExtractor:
    """
    Extracteur d'entités
    """

    def __init__(self):
        """Initialise l'extracteur """
        self.nlp_model = load_spacy_model()
        self._load_patterns()

    def _load_patterns(self):
        """Charge les patterns enrichis """
        # Charger tous les patterns en mode auto
        # dans le futur version nous pourions garder une seule langue pour plus de coherence ou ameliorer le 
        # modele en francais
        self.all_patterns = get_patterns('auto', 'all')

        # Patterns spécifiques par langue
        self.patterns_fr = get_patterns('fr', 'all')
        self.patterns_en = get_patterns('en', 'all')

    def _extract_entities(self, query: str, language: str) -> List[ParsedEntity]:
        """Extrait les entités nommées avec patterns enrichis """
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
        """Extraction d'entités avec spaCy """
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
        """Mappe les labels spaCy vers nos types d'entités """
        return SPACY_LABEL_MAPPING.get(label)

    def _extract_entities_patterns(self, query: str, language: str) -> List[ParsedEntity]:
        """Extraction d'entités avec patterns enrichis """
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
                    if is_valid_email(email):
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
        """Validation intelligente des noms de personnes """
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

    def _deduplicate_entities(self, entities: List[ParsedEntity]) -> List[ParsedEntity]:
        """Supprime les entités dupliquées en gardant celle avec le meilleur score """

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

    def _validate_entities(self, entities: List[ParsedEntity], language: str) -> List[ParsedEntity]:
        """Valide et filtre les entités extraites """
        validated_entities = []

        for entity in entities:
            is_valid = True

            # Validation spécifique par type
            if entity.type == 'PERSON':
                is_valid = self._is_valid_person_name(entity.value, language)
            elif entity.type == 'EMAIL':
                is_valid = is_valid_email(entity.value)
            elif entity.type == 'TEMPORAL':
                # Vérifier que la date est raisonnable
                try:
                    from datetime import datetime
                    datetime.strptime(entity.value, '%Y-%m-%d')
                except ValueError:
                    is_valid = False

            if is_valid:
                validated_entities.append(entity)

        return validated_entities

    def _normalize_temporal_entity(self, text: str, config: dict, timezone: str = "UTC") -> str:
        """
        Normalise une entité temporelle en date ISO avec support timezone et plages.
        """
        try:
            import pytz
            from datetime import datetime, timedelta
            import calendar
            from .base_parser import get_month_number

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
                        month_num = get_month_number(month)
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
                    month_num = get_month_number(month_name)
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