"""
Configuration pour le processeur de graphe d'emails.
"""

# Configuration du traitement par lots
BATCH_CONFIG = {
    'progress_log_interval': 1000,  # Intervalle pour logs d'avancement
    'default_max_emails': None,     # Limite par défaut (None = pas de limite)
}

# Configuration des relations et poids
RELATION_WEIGHTS = {
    'sent_central_user': 3.0,    # Poids pour messages envoyés par l'utilisateur central
    'sent_normal': 1.0,          # Poids normal pour envoi
    'received': 1.0,             # Poids pour réception
    'cc': 0.8,                   # Poids pour CC
    'bcc': 0.6,                  # Poids pour BCC
    'part_of_thread': 1.0        # Poids pour appartenance au thread
}

# Configuration de l'analyse
ANALYSIS_CONFIG = {
    'top_contacts_limit': 10,
    'top_threads_limit': 5,
    'include_stats': True,
    'include_metadata': True
}

# Messages d'erreur standardisés
ERROR_MESSAGES = {
    'json_parse_error': 'Erreur lors du parsing JSON',
    'email_processing_error': 'Erreur lors du traitement de l\'email',
    'graph_building_error': 'Erreur lors de la construction du graphe',
    'analysis_error': 'Erreur lors de l\'analyse du graphe'
}