"""
Gestionnaire principal pour les nœuds utilisateur.
"""

from ...logging_service import logger
from .user_validator import validate_email_address, find_existing_user_by_email
from .user_transformer import create_user_id, build_user_attributes, extract_email_participants
from .relation_service import UserRelationService


class UserNodeManager:
    """Gestionnaire pour la création et la manipulation des nœuds utilisateur."""

    def __init__(self, graph):
        """
        Initialise le gestionnaire de nœuds utilisateur

        Args:
            graph: Instance NetworkX pour stocker les nœuds
        """
        self.graph = graph
        self.central_user_email = None
        self.email_cache = {}  # Cache de normalisation des emails
        self.relation_service = UserRelationService(graph)

    def set_graph(self, graph):
        """
        Met à jour l'instance de graphe

        Args:
            graph: Nouvelle instance NetworkX
        """
        self.graph = graph
        self.relation_service.set_graph(graph)

    def set_central_user(self, central_user_email):
        """
        Définit l'utilisateur central pour le graphe

        Args:
            central_user_email: Email de l'utilisateur central
        """
        self.central_user_email = validate_email_address(central_user_email)

    def create_user(self, email_address):
        """
        Crée ou récupère un noeud utilisateur

        Args:
            email_address (str): Adresse email

        Returns:
            str|None: ID de l'utilisateur
        """
        # Validation de l'email
        clean_email = validate_email_address(email_address)
        if not clean_email:
            return None

        # Vérifier si l'utilisateur existe déjà
        existing_user_id = find_existing_user_by_email(self.graph, clean_email)
        if existing_user_id:
            return existing_user_id

        # Déterminer si c'est l'utilisateur central
        is_central_user = (self.central_user_email and
                          clean_email == self.central_user_email)

        # Créer un nouvel utilisateur
        user_id = create_user_id()
        user_attributes = build_user_attributes(email_address, is_central_user)

        # Ajouter le noeud au graphe
        self.graph.add_node(user_id, **user_attributes)

        # Logger la création
        logger.user_created(user_id, clean_email, is_central_user)

        return user_id

    def update_connection_strength(self, user1_id, user2_id, weight=1.0):
        """
        Met à jour la force de connexion entre deux utilisateurs

        Args:
            user1_id (str): ID du premier utilisateur
            user2_id (str): ID du second utilisateur
            weight (float): Poids de la connexion
        """
        self.relation_service.update_connection_strength(
            user1_id, user2_id, weight, self.central_user_email
        )

    def create_recipient_relationships(self, email_data, from_user_id=None):
        """
        Crée les relations entre tous les participants d'un email
        (expéditeur et destinataires)

        Args:
            email_data (dict): Données d'un email
            from_user_id (str): ID de l'utilisateur expéditeur (si déjà connu)

        Returns:
            list: Liste des relations créées
        """
        relations = []

        # Obtenir l'expéditeur
        participants = extract_email_participants(email_data)
        from_email = participants['from']

        if not from_email and not from_user_id:
            return relations

        # Créer ou récupérer l'utilisateur expéditeur si nécessaire
        if not from_user_id:
            from_user_id = self.create_user(from_email)
            if not from_user_id:
                return relations

        # Déléguer la création des relations au service spécialisé
        relations = self.relation_service.create_recipient_relationships(
            email_data, from_user_id, self.central_user_email
        )

        return relations