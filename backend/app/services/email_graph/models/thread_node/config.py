"""
Configuration pour les nœuds de thread.
"""

# Attributs par défaut pour les threads
DEFAULT_THREAD_ATTRIBUTES = {
    'type': 'thread',
    'first_message_id': '',
    'message_count': 0,
    'last_message_date': '',
    'participants': [],
    'topics': [],
    'subject': ''
}

# Champs requis pour créer un thread
REQUIRED_THREAD_FIELDS = ['Thread-ID']

# Champs pour la mise à jour des threads
THREAD_UPDATE_FIELDS = {
    'message_count': 'message_count',
    'last_message_date': 'last_message_date',
    'participants': 'participants',
    'topics': 'topics'
}

# Clés de date alternatives pour la recherche
DATE_FIELD_PRIORITY = [
    'Internal-Date',
    'Date',
    'timestamp'
]