"""
Configuration et imports de base pour le parsing 
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import pytz
import calendar


# Import conditionnel de spaCy pour NER 
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    raise RuntimeError("spaCy n'est pas installé ")


# === CONSTANTES ET CONFIGURATIONS  ===

# Mapping des labels spaCy vers nos types d'entités 
SPACY_LABEL_MAPPING = {
    'PERSON': 'PERSON',
    'PER': 'PERSON',
    'DATE': 'TEMPORAL',
    'TIME': 'TEMPORAL',
    'ORG': 'ORGANIZATION',
    'LOC': 'LOCATION',
    'MISC': 'MISC'
}

# Mois français vers numéros 
MONTHS_FR = {
    'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4,
    'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8,
    'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12
}

# Mois anglais vers numéros 
MONTHS_EN = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12
}

# Indicateurs de langue française 
FRENCH_INDICATORS = [
    'emails', 'mails', 'messages', 'courriels', 'de', 'du', 'des', 'avec', 'dans',
    'par', 'pour', 'hier', 'aujourd', 'demain', 'semaine', 'mois', 'année',
    'pièce jointe', 'expéditeur', 'destinataire', 'conversation', 'réunion',
    'envoyé', 'envoyés', 'sans', 'entre'
]

# Indicateurs de langue anglaise 
ENGLISH_INDICATORS = [
    'email', 'mail', 'message', 'from', 'to', 'with', 'in', 'by', 'for',
    'yesterday', 'today', 'tomorrow', 'week', 'month', 'year',
    'attachment', 'sender', 'recipient', 'conversation', 'meeting',
    'sent', 'without', 'between'
]


# === FONCTIONS UTILITAIRES COMMUNES ===

def load_spacy_model():
    """Charge le modèle spaCy si disponible """
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


def get_month_number(month_name: str) -> int:
    """Convertit un nom de mois en numéro """
    month_lower = month_name.lower()
    return MONTHS_FR.get(month_lower, MONTHS_EN.get(month_lower, 1))


def is_valid_email(email: str) -> bool:
    """Validation d'adresse email """
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))


def is_valid_date_format(date_str: str) -> bool:
    """Vérifie le format de date YYYY-MM-DD """
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except (ValueError, TypeError):
        return False


def clean_query(query: str) -> str:
    """Nettoie et normalise la requête """
    # Supprimer caractères spéciaux inutiles mais garder @ pour emails
    cleaned = re.sub(r'[^\w\s@.-]', ' ', query)

    # Normaliser les espaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    # Convertir en minuscules pour pattern matching
    return cleaned.lower()

