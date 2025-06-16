"""
Service de gestion des relations entre utilisateurs.
"""

from ...logging_service import logger
from .config import RELATION_WEIGHTS
from .user_validator import validate_relation_participants


class UserRelationService:
    """Service pour gérer les relations entre utilisateurs"""

    def __init__(self, graph):
        self.graph = graph

    def set_graph(self, graph):
        """Met à jour l'instance de graphe"""
        self.graph = graph

    def create_user_relation(self, source_id, target_id, relation_type, weight):
        """
        Crée une relation entre deux utilisateurs s'ils existent

        Args:
            source_id (str): ID de l'utilisateur source
            target_id (str): ID de l'utilisateur cible
            relation_type (str): Type de la relation
            weight (float): Poids de la relation

        Returns:
            dict|None: Relation créée ou None
        """
        # Validation des participants
        if not validate_relation_participants(self.graph, source_id, target_id):
            return None

        # Vérifier si une relation du même type existe déjà
        edges_data = self.graph.get_edge_data(source_id, target_id)

        if edges_data:  # Si des arêtes existent entre ces nœuds
            # Rechercher une arête avec le même type de relation
            for key, data in edges_data.items():
                if data.get("type") == relation_type:
                    # Mettre à jour le poids de cette arête spécifique
                    self.graph[source_id][target_id][key]["weight"] += weight
                    logger.relation_created(relation_type, source_id, target_id,
                                            self.graph[source_id][target_id][key]["weight"])
                    return self.graph[source_id][target_id][key]

        # Si aucune relation de ce type n'existe, en créer une nouvelle
        edge_data = {
            "type": relation_type,
            "weight": weight
        }
        self.graph.add_edge(source_id, target_id, **edge_data)

        logger.relation_created(relation_type, source_id, target_id, weight)

        # Retourner les données de la nouvelle relation
        return edge_data

    def update_connection_strength(self, user1_id, user2_id, weight=1.0, central_user_email=None):
        """
        Met à jour la force de connexion entre deux utilisateurs

        Args:
            user1_id (str): ID du premier utilisateur
            user2_id (str): ID du second utilisateur
            weight (float): Poids de la connexion
            central_user_email (str): Email de l'utilisateur central
        """
        if not central_user_email:
            return

        user1_data = self.graph.nodes.get(user1_id, {})
        user2_data = self.graph.nodes.get(user2_id, {})

        # Mise à jour de la force de connexion pour l'utilisateur qui n'est pas central
        if user1_data.get("is_central_user", False):
            if "connection_strength" in user2_data:
                user2_data["connection_strength"] = user2_data.get("connection_strength", 0) + weight

        elif user2_data.get("is_central_user", False):
            if "connection_strength" in user1_data:
                user1_data["connection_strength"] = user1_data.get("connection_strength", 0) + weight

    def get_relation_weight(self, relation_type, is_central_sender):
        """
        Récupère le poids d'une relation selon son type et l'état de l'expéditeur

        Args:
            relation_type (str): Type de relation
            is_central_sender (bool): Si l'expéditeur est l'utilisateur central

        Returns:
            float: Poids de la relation
        """
        if relation_type not in RELATION_WEIGHTS:
            return 1.0

        weight_config = RELATION_WEIGHTS[relation_type]
        return weight_config["central_sender"] if is_central_sender else weight_config["normal"]

    def create_recipient_relationships(self, email_data, from_user_id, central_user_email):
        """
        Crée les relations entre un expéditeur et tous les destinataires d'un email

        Args:
            email_data (dict): Données d'email
            from_user_id (str): ID de l'utilisateur expéditeur
            central_user_email (str): Email de l'utilisateur central

        Returns:
            list: Liste des relations créées
        """
        relations = []

        if not from_user_id:
            return relations

        # Obtenir les infos de l'expéditeur
        from_user_data = self.graph.nodes.get(from_user_id, {})
        is_central_sender = from_user_data.get("is_central_user", False)

        # Extraire les participants
        from .user_transformer import extract_email_participants
        participants = extract_email_participants(email_data)

        # Créer les utilisateurs et relations pour chaque type de destinataire
        relation_configs = [
            (participants['to'], "EMAILED"),
            (participants['cc'], "EMAILED_CC"),
            (participants['bcc'], "EMAILED_BCC")
        ]

        for email_list, relation_type in relation_configs:
            for email in email_list:
                # Créer l'utilisateur destinataire
                from .user_manager import UserNodeManager
                user_manager = UserNodeManager(self.graph)
                user_manager.set_central_user(central_user_email)
                to_user_id = user_manager.create_user(email)

                if to_user_id:
                    # Déterminer le poids
                    weight = self.get_relation_weight(relation_type, is_central_sender)

                    # Créer la relation
                    relation = self.create_user_relation(from_user_id, to_user_id,
                                                         relation_type, weight)
                    if relation:
                        relations.append(relation)
                        self.update_connection_strength(from_user_id, to_user_id,
                                                        weight, central_user_email)

        return relations