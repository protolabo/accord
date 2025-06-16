"""
Service de transformation des données temporelles et autres utilitaires.
"""

import re
import math
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import pytz

from ..config import TEMPORAL_CONFIG


def normalize_temporal_entity(text: str, config: Dict[str, Any], timezone: str = "UTC") -> str:
    """
    Normalise une entité temporelle en date ISO avec support timezone

    Args:
        text (str): Texte de l'entité temporelle
        config (dict): Configuration de l'entité
        timezone (str): Timezone à utiliser

    Returns:
        str: Date au format ISO
    """
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
            if days_ahead <= 0:  # Si c'est aujourd'hui ou dans le passé, prendre la semaine prochaine
                days_ahead += 7
            target_date = now + timedelta(days=days_ahead)
            return target_date.strftime('%Y-%m-%d')

        elif config['type'] == 'month':
            # Mois spécifique dans l'année courante
            target_month = config['month']
            target_date = now.replace(month=target_month, day=1)
            return target_date.strftime('%Y-%m-%d')

    except Exception as e:
        print(f"⚠️ Erreur normalisation temporelle: {e}")

    # Fallback: retourner le texte original
    return text


class TransformationService:
    """Service pour diverses transformations de données"""

    def __init__(self):
        pass

    def clean_and_normalize_text(self, text: str) -> str:
        """Nettoie et normalise un texte"""
        if not text:
            return ""

        # Supprimer caractères spéciaux mais garder @ pour emails
        cleaned = re.sub(r'[^\w\s@.-]', ' ', text)

        # Normaliser les espaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        return cleaned.lower()

    def extract_email_components(self, email: str) -> Dict[str, str]:
        """
        Extrait les composants d'une adresse email

        Args:
            email (str): Adresse email

        Returns:
            dict: Composants (local, domain, name)
        """
        if not email or '@' not in email:
            return {'local': '', 'domain': '', 'name': ''}

        # Nettoyer l'email
        clean_email = email.strip().lower()

        # Séparer local et domaine
        local, domain = clean_email.split('@', 1)

        # Extraire un nom probable à partir de la partie locale
        name = local.replace('.', ' ').replace('_', ' ').replace('-', ' ')
        name = ' '.join(word.capitalize() for word in name.split())

        return {
            'local': local,
            'domain': domain,
            'name': name
        }

    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calcule la similarité entre deux textes (Jaccard simplifié)

        Args:
            text1 (str): Premier texte
            text2 (str): Deuxième texte

        Returns:
            float: Score de similarité entre 0 et 1
        """
        if not text1 or not text2:
            return 0.0

        # Tokeniser les textes
        tokens1 = set(re.findall(r'\b\w+\b', text1.lower()))
        tokens2 = set(re.findall(r'\b\w+\b', text2.lower()))

        if not tokens1 or not tokens2:
            return 0.0

        # Calculer la similarité de Jaccard
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)

        return len(intersection) / len(union) if union else 0.0

    def normalize_person_name(self, name: str) -> str:
        """
        Normalise un nom de personne

        Args:
            name (str): Nom à normaliser

        Returns:
            str: Nom normalisé
        """
        if not name:
            return ""

        # Nettoyer et formater
        cleaned = re.sub(r'[^\w\s\-\']', '', name)
        words = cleaned.split()

        # Capitaliser chaque mot
        normalized_words = []
        for word in words:
            if word:
                # Gérer les cas spéciaux comme O'Connor, Jean-Pierre
                if '-' in word:
                    parts = word.split('-')
                    word = '-'.join(part.capitalize() for part in parts)
                elif "'" in word:
                    parts = word.split("'")
                    word = "'".join(part.capitalize() for part in parts)
                else:
                    word = word.capitalize()

                normalized_words.append(word)

        return ' '.join(normalized_words)

    def expand_topic_synonyms(self, topic: str, synonyms_map: Dict[str, list]) -> list:
        """
        Étend un topic avec ses synonymes

        Args:
            topic (str): Topic de base
            synonyms_map (dict): Mapping des synonymes

        Returns:
            list: Liste étendue incluant les synonymes
        """
        expanded = [topic.lower()]

        # Chercher les synonymes
        for main_topic, synonyms in synonyms_map.items():
            if topic.lower() == main_topic or topic.lower() in synonyms:
                expanded.append(main_topic)
                expanded.extend(synonyms)

        return list(set(expanded))  # Dédupliquer

    def calculate_freshness_score(self, date_str: str, decay_days: int = 30) -> float:
        """
        Calcule un score de fraîcheur basé sur la date

        Args:
            date_str (str): Date au format ISO
            decay_days (int): Nombre de jours pour le decay

        Returns:
            float: Score entre 0 et 1
        """
        if not date_str:
            return 0.0

        try:
            message_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            days_old = (datetime.now(pytz.UTC) - message_date).days
            return math.exp(-days_old / decay_days)
        except Exception:
            return 0.0

    def merge_filters(self, base_filters: Dict[str, Any], new_filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fusionne deux dictionnaires de filtres de manière intelligente

        Args:
            base_filters (dict): Filtres de base
            new_filters (dict): Nouveaux filtres

        Returns:
            dict: Filtres fusionnés
        """
        merged = base_filters.copy()

        for key, value in new_filters.items():
            if key in merged:
                # Logique de fusion spécifique selon le type
                if isinstance(value, list) and isinstance(merged[key], list):
                    # Fusionner les listes
                    merged[key] = list(set(merged[key] + value))
                elif isinstance(value, dict) and isinstance(merged[key], dict):
                    # Fusionner les dictionnaires
                    merged[key].update(value)
                else:
                    # Remplacer la valeur
                    merged[key] = value
            else:
                merged[key] = value

        return merged

    def validate_and_format_limit(self, limit: Any, default: int = 10, max_limit: int = 100) -> int:
        """
        Valide et formate une limite

        Args:
            limit: Limite à valider
            default (int): Valeur par défaut
            max_limit (int): Limite maximale

        Returns:
            int: Limite validée
        """
        if limit is None:
            return default

        try:
            limit_int = int(limit)
            return max(1, min(limit_int, max_limit))
        except (ValueError, TypeError):
            return default

    def extract_query_keywords(self, query: str, min_length: int = 3) -> list:
        """
        Extrait les mots-clés significatifs d'une requête

        Args:
            query (str): Requête à analyser
            min_length (int): Longueur minimale des mots

        Returns:
            list: Liste des mots-clés
        """
        if not query:
            return []

        # Nettoyer et tokeniser
        cleaned = self.clean_and_normalize_text(query)
        words = re.findall(r'\b\w+\b', cleaned)

        # Filtrer par longueur et supprimer les mots courants
        stopwords = {'le', 'la', 'les', 'de', 'du', 'des', 'et', 'ou', 'à', 'avec', 'sans',
                     'the', 'a', 'an', 'and', 'or', 'to', 'with', 'without', 'from', 'in'}

        keywords = []
        for word in words:
            if len(word) >= min_length and word.lower() not in stopwords:
                keywords.append(word)

        return keywords