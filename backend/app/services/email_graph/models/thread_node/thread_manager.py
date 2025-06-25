"""
Gestionnaire principal pour les nœuds de thread.
"""

from ...logging_service import logger
from .thread_validator import validate_thread_id, validate_thread_data, check_thread_exists
from .thread_service import ThreadService


class ThreadNodeManager:
    """Gestionnaire pour la création et la manipulation des nœuds de thread."""

    def __init__(self, graph):
        """
        Initialise le gestionnaire de nœuds de thread

        Args:
            graph: Instance NetworkX pour stocker les nœuds
        """
        self.graph = graph
        self.thread_service = ThreadService(graph)

    def set_graph(self, graph):
        """
        Met à jour l'instance de graphe

        Args:
            graph: Nouvelle instance NetworkX
        """
        self.graph = graph
        self.thread_service.set_graph(graph)

    def create_thread(self, email_data):
        """
        Crée ou met à jour un noeud de thread

        Args:
            email_data (dict): Données d'un email

        Returns:
            str|None: ID du thread
        """
        # Validation des données
        if not validate_thread_data(email_data):
            logger.logger.error("❌ Données d'email invalides pour créer un thread")
            return None

        # Validation de l'ID du thread
        thread_id = validate_thread_id(email_data)
        if not thread_id:
            return None

        # Déterminer s'il faut créer ou mettre à jour
        if check_thread_exists(self.graph, thread_id):
            return self.thread_service.update_existing_thread(email_data, thread_id)
        else:
            return self.thread_service.create_new_thread(email_data, thread_id)

    def get_thread_info(self, thread_id):
        """
        Récupère les informations complètes d'un thread

        Args:
            thread_id (str): ID du thread

        Returns:
            dict|None: Informations du thread
        """
        if not check_thread_exists(self.graph, thread_id):
            logger.logger.warning(f"⚠️ Thread non trouvé: {thread_id}")
            return None

        return self.graph.nodes[thread_id]

    def get_thread_statistics(self, thread_id):
        """
        Récupère les statistiques d'un thread

        Args:
            thread_id (str): ID du thread

        Returns:
            dict|None: Statistiques du thread
        """
        return self.thread_service.get_thread_stats(thread_id)

    def list_thread_participants(self, thread_id):
        """
        Liste les participants d'un thread

        Args:
            thread_id (str): ID du thread

        Returns:
            list: Liste des participants
        """
        thread_info = self.get_thread_info(thread_id)
        if thread_info:
            return thread_info.get('participants', [])
        return []

    def get_thread_message_count(self, thread_id):
        """
        Récupère le nombre de messages dans un thread

        Args:
            thread_id (str): ID du thread

        Returns:
            int: Nombre de messages
        """
        thread_info = self.get_thread_info(thread_id)
        if thread_info:
            return thread_info.get('message_count', 0)
        return 0