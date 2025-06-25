"""
Services de gestion des threads (création et mise à jour).
"""

from ...logging_service import logger
from .thread_validator import check_thread_exists, validate_message_for_thread
from .thread_transformer import (
    build_new_thread_attributes,
    parse_thread_date,
    update_thread_participants,
    should_update_date,
    update_thread_topics
)


class ThreadService:
    """Service pour la gestion des opérations sur les threads"""

    def __init__(self, graph):
        self.graph = graph

    def set_graph(self, graph):
        """Met à jour l'instance de graphe"""
        self.graph = graph

    def create_new_thread(self, email_data, thread_id):
        """
        Crée un nouveau thread

        Args:
            email_data (dict): Données d'email
            thread_id (str): ID du thread

        Returns:
            str: ID du thread créé
        """
        # Valider que le message peut être ajouté
        is_valid, message_id = validate_message_for_thread(email_data)
        if not is_valid:
            return None

        # Construire les attributs du thread
        thread_attributes = build_new_thread_attributes(email_data, thread_id)

        # Ajouter le noeud au graphe
        self.graph.add_node(thread_id, **thread_attributes)

        # Logger la création
        logger.thread_created(thread_id, 1)

        return thread_id

    def update_existing_thread(self, email_data, thread_id):
        """
        Met à jour un thread existant

        Args:
            email_data (dict): Données d'email
            thread_id (str): ID du thread

        Returns:
            str: ID du thread mis à jour
        """
        if not check_thread_exists(self.graph, thread_id):
            logger.logger.error(f"❌ Tentative de mise à jour d'un thread inexistant: {thread_id}")
            return None

        thread_data = self.graph.nodes[thread_id]

        # 1. Incrémenter le compteur de messages
        thread_data["message_count"] = thread_data.get("message_count", 0) + 1

        # 2. Mettre à jour la date du dernier message
        self._update_thread_date(thread_data, email_data, thread_id)

        # 3. Mettre à jour les participants
        self._update_thread_participants(thread_data, email_data)

        # 4. Mettre à jour les topics
        self._update_thread_topics(thread_data, email_data)

        # Logger la mise à jour
        logger.logger.info(f"✅ Thread mis à jour: {thread_id} ({thread_data['message_count']} messages)")

        return thread_id

    def _update_thread_date(self, thread_data, email_data, thread_id):
        """
        Met à jour la date du dernier message si nécessaire

        Args:
            thread_data (dict): Données du thread
            email_data (dict): Données d'email
            thread_id (str): ID du thread
        """
        new_date = parse_thread_date(email_data, thread_id)
        current_date = thread_data.get("last_message_date", "")

        if should_update_date(current_date, new_date):
            thread_data["last_message_date"] = new_date
            logger.logger.info(f"📅 Date mise à jour pour thread {thread_id}: {new_date}")

    def _update_thread_participants(self, thread_data, email_data):
        """
        Met à jour les participants du thread

        Args:
            thread_data (dict): Données du thread
            email_data (dict): Données d'email
        """
        current_participants = thread_data.get("participants", [])
        updated_participants = update_thread_participants(current_participants, email_data)
        thread_data["participants"] = updated_participants

    def _update_thread_topics(self, thread_data, email_data):
        """
        Met à jour les topics du thread

        Args:
            thread_data (dict): Données du thread
            email_data (dict): Données d'email
        """
        current_topics = thread_data.get("topics", [])
        updated_topics = update_thread_topics(current_topics, email_data)
        thread_data["topics"] = updated_topics

    def get_thread_stats(self, thread_id):
        """
        Récupère les statistiques d'un thread

        Args:
            thread_id (str): ID du thread

        Returns:
            dict|None: Statistiques du thread
        """
        if not check_thread_exists(self.graph, thread_id):
            return None

        thread_data = self.graph.nodes[thread_id]

        return {
            'message_count': thread_data.get('message_count', 0),
            'participant_count': len(thread_data.get('participants', [])),
            'last_message_date': thread_data.get('last_message_date', ''),
            'topic_count': len(thread_data.get('topics', [])),
            'subject': thread_data.get('subject', '')
        }