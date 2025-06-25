"""
Configuration pour les nœuds utilisateur et les relations.
"""

# Configuration des poids des relations
RELATION_WEIGHTS = {
    "EMAILED": {
        "central_sender": 3.0,  # Poids fort si l'expéditeur est l'utilisateur central
        "normal": 1.0  # Poids normal sinon
    },
    "EMAILED_CC": {
        "central_sender": 1.5,  # Poids pour CC si l'expéditeur est l'utilisateur central
        "normal": 0.5  # Poids normal sinon
    },
    "EMAILED_BCC": {
        "central_sender": 1.0,  # Poids pour BCC si l'expéditeur est l'utilisateur central
        "normal": 0.3  # Poids normal sinon
    },
}

# Types de relations supportées
RELATION_TYPES = ["EMAILED", "EMAILED_CC", "EMAILED_BCC"]

# Attributs par défaut pour les utilisateurs
DEFAULT_USER_ATTRIBUTES = {
    'type': 'user',
    'email': '',
    'name': '',
    'domain': '',
    'is_central_user': False,
    'connection_strength': 0.0
}

# Préfixe pour les IDs utilisateur
USER_ID_PREFIX = "user-"