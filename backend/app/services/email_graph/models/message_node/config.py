"""
Configuration pour les nœuds de message.
"""

# Attributs par défaut pour les messages
DEFAULT_MESSAGE_ATTRIBUTES = {
    'type': 'message',
    'thread_id': '',
    'date': '',
    'subject': '',
    'content': '',
    'from': '',
    'from_email': '',  # temporaire
    'to': [],
    'cc': [],
    'bcc': [],
    'has_attachments': False,
    'attachment_count': 0,
    'is_important': False,
    'is_unread': True,
    'topics': [],
    'labels': [],
    'categories': [],
    'attachments': [],
    'snippet': ''
}

# Champs obligatoires pour un message valide
REQUIRED_MESSAGE_FIELDS = ['Message-ID']

# Champs optionnels avec valeurs par défaut
OPTIONAL_MESSAGE_FIELDS = {
    'Subject': '',
    'Content': '',
    'From': '',
    'To': '',
    'Cc': '',
    'Bcc': '',
    'Date': '',
    'Thread-ID': ''
}

# Mapping des clés d'entrée vers les attributs du nœud
FIELD_MAPPING = {
    'Message-ID': 'message_id',
    'Thread-ID': 'thread_id',
    'Date': 'date',
    'Internal-Date': 'internal_date',
    'Subject': 'subject',
    'Content': 'content',
    'From': 'from',
    'To': 'to',
    'Cc': 'cc',
    'Bcc': 'bcc',
    'Labels': 'labels',
    'Categories': 'categories',
    'Attachments': 'attachments',
    'Snippet': 'snippet'
}

# Formats de date supportés
SUPPORTED_DATE_FORMATS = [
    '%Y-%m-%dT%H:%M:%S%z',
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%d'
]