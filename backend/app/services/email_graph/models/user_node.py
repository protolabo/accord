"""
Gestionnaire de nœuds utilisateur pour le graphe d'emails.
Gère la création des utilisateurs et les relations entre eux.
"""

import uuid
from ..utils.email_utils import normalize_email, extract_email_parts


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
        self.email_cache = {}  # Normalisation des emails

        # Configuration des poids des relations
        self.relation_weights = {
            # Poids pour relations directes
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

    def set_graph(self, graph):
        """
        Met à jour l'instance de graphe

        Args:
            graph: Nouvelle instance NetworkX
        """
        self.graph = graph

    def set_central_user(self, central_user_email):
        """
        Définit l'utilisateur central pour le graphe

        Args:
            central_user_email: Email de l'utilisateur central
        """
        self.central_user_email = normalize_email(central_user_email) if central_user_email else None

    def create_user(self, email_address):
        """
        Crée ou récupère un noeud utilisateur

        Args:
            email_address (str): Adresse email

        Returns:
            str: ID de l'utilisateur
        """
        if not email_address:
            return None

        clean_email = normalize_email(email_address)

        # Vérifier si l'utilisateur existe déjà
        for node, data in self.graph.nodes(data=True):
            if data.get("type") == "user" and data.get("email") == clean_email:
                return node

        # Extraire les parties de l'email
        email, domain, name = extract_email_parts(email_address)

        # Créer un nouvel utilisateur
        user_id = f"user-{str(uuid.uuid4())}"

        # Déterminer si c'est l'utilisateur central
        is_central_user = False
        if self.central_user_email and clean_email == self.central_user_email:
            is_central_user = True

        # Ajouter le noeud au graphe
        self.graph.add_node(
            user_id,
            type="user",
            email=clean_email,
            name=name,
            domain=domain,
            is_central_user=is_central_user,
            connection_strength=0.0
        )

        return user_id

    def update_connection_strength(self, user1_id, user2_id, weight=1.0):
        """
        Met à jour la force de connexion entre deux utilisateurs

        Args:
            user1_id (str): ID du premier utilisateur
            user2_id (str): ID du second utilisateur
            weight (float): Poids de la connexion
        """
        # Vérifier si l'un des utilisateurs est l'utilisateur central
        if not self.central_user_email:
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
        from_email = email_data.get("From", "")

        # je ne comprends pas le fonctionnement de ce code
        if not from_email and not from_user_id:
            return relations

        # Créer ou récupérer l'utilisateur expéditeur si nécessaire
        if not from_user_id:
            from_user_id = self.create_user(from_email)
            if not from_user_id:
                return relations

        # Obtenir les infos de l'expéditeur
        from_user_data = self.graph.nodes.get(from_user_id, {})

        # récupère la valeur de la clé "is_central_user" si elle existe,
        # sinon retourne la valeur par défaut False
        is_central_sender = from_user_data.get("is_central_user", False)

        # Extraire les listes de destinataires
        to_emails = email_data.get("To", "").split(",") if email_data.get("To") else []
        cc_emails = email_data.get("Cc", "").split(",") if email_data.get("Cc") else []
        bcc_emails = email_data.get("Bcc", "").split(",") if email_data.get("Bcc") else []

        # Nettoyer les listes
        to_emails = [e.strip() for e in to_emails if e.strip()]
        cc_emails = [e.strip() for e in cc_emails if e.strip()]
        bcc_emails = [e.strip() for e in bcc_emails if e.strip()]

        # Créer les utilisateurs pour tous les destinataires
        to_user_ids = [self.create_user(email) for email in to_emails]
        cc_user_ids = [self.create_user(email) for email in cc_emails]
        bcc_user_ids = [self.create_user(email) for email in bcc_emails]

        # Filtrer les None
        """
        Cette ligne filtre les valeurs None ou vides de la liste. Quand create_user() est appelé pour chaque email, il peut retourner None si:
        L'adresse email est invalide
        Une erreur se produit pendant la création
        L'email est vide

        Ce filtrage garantit que seuls les IDs valides sont utilisés pour créer des relations.
        """

        to_user_ids = [uid for uid in to_user_ids if uid]
        cc_user_ids = [uid for uid in cc_user_ids if uid]
        bcc_user_ids = [uid for uid in bcc_user_ids if uid]


        # 1. Créer les relations Expéditeur -> Destinataires

        # Expéditeur -> To
        for to_user_id in to_user_ids:
            # defini le poids grace au donnee en parametre
            weight = self.relation_weights["EMAILED"]["central_sender"] if is_central_sender else \
            self.relation_weights["EMAILED"]["normal"]

            relation = self._create_user_relation(
                from_user_id,
                to_user_id,
                "EMAILED",
                weight
            )
            if relation:
                relations.append(relation)
                self.update_connection_strength(from_user_id, to_user_id, weight)

        # Expéditeur -> CC
        for cc_user_id in cc_user_ids:
            weight = self.relation_weights["EMAILED_CC"]["central_sender"] if is_central_sender else \
            self.relation_weights["EMAILED_CC"]["normal"]

            relation = self._create_user_relation(
                from_user_id,
                cc_user_id,
                "EMAILED_CC",
                weight
            )
            if relation:
                relations.append(relation)
                self.update_connection_strength(from_user_id, cc_user_id, weight)

        # Expéditeur -> BCC
        for bcc_user_id in bcc_user_ids:
            weight = self.relation_weights["EMAILED_BCC"]["central_sender"] if is_central_sender else \
            self.relation_weights["EMAILED_BCC"]["normal"]

            relation = self._create_user_relation(
                from_user_id,
                bcc_user_id,
                "EMAILED_BCC",
                weight
            )
            if relation:
                relations.append(relation)
                self.update_connection_strength(from_user_id, bcc_user_id, weight)




        return relations

    def _create_user_relation(self, source_id, target_id, relation_type, weight):
        """
        Crée une relation entre deux utilisateurs s'ils existent

        Args:
            source_id (str): ID de l'utilisateur source
            target_id (str): ID de l'utilisateur cible
            relation_type (str): Type de la relation
            weight (float): Poids de la relation

        Returns:
            dict: Relation créée ou None
        """
        # Vérifier que les utilisateurs existent
        if not self.graph.has_node(source_id) or not self.graph.has_node(target_id):
            return None

        # Ne pas créer de relation avec soi-même
        if source_id == target_id:
            return None

        # Créer la relation
        edge_key = None
        if self.graph.has_edge(source_id, target_id, key=edge_key):
            # Si la relation existe déjà, mettre à jour le poids
            edge_data = self.graph.get_edge_data(source_id, target_id, key=edge_key)
            # Augmenter le poids existant (cumul de l'importance)
            edge_data["weight"] += weight
            return edge_data
        else:
            # Créer une nouvelle relation
            edge_data = {
                "type": relation_type,
                "weight": weight
            }
            self.graph.add_edge(source_id, target_id, **edge_data)
            return edge_data
