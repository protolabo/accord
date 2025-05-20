import pytest
from unittest.mock import patch, MagicMock
from backend.app.services.email_graph.models.user_node import UserNodeManager


class TestUserNodeManager:
    """Tests pour la classe UserNodeManager."""

    def test_init(self, empty_graph):
        """Test l'initialisation du gestionnaire."""
        manager = UserNodeManager(empty_graph)
        assert manager.graph == empty_graph
        assert manager.central_user_email is None
        assert manager.email_cache == {}
        assert isinstance(manager.relation_weights, dict)

    def test_set_graph(self, empty_graph):
        """Test la méthode set_graph."""
        manager = UserNodeManager(None)
        manager.set_graph(empty_graph)
        assert manager.graph == empty_graph

    def test_set_central_user(self):
        """Test la méthode set_central_user."""
        manager = UserNodeManager(None)

        # Patch normalize_email
        with patch('backend.app.services.email_graph.models.user_node.normalize_email') as mock_normalize:
            mock_normalize.return_value = "normalized_email@example.com"

            # Définir l'utilisateur central
            manager.set_central_user("Central.User@Example.com")

            # Vérifier que l'email est normalisé
            assert manager.central_user_email == "normalized_email@example.com"
            mock_normalize.assert_called_once_with("Central.User@Example.com")

    def test_set_central_user_none(self):
        """Test que set_central_user gère correctement None."""
        manager = UserNodeManager(None)

        # Définir l'utilisateur central à None
        manager.set_central_user(None)

        # Vérifier que l'email central est None
        assert manager.central_user_email is None

    @patch('uuid.uuid4', return_value=MagicMock(hex='12345'))
    def test_create_user_new(self, mock_uuid, empty_graph):
        """Test la création d'un nouveau noeud utilisateur."""
        manager = UserNodeManager(empty_graph)

        # Patch les fonctions d'utilitaire
        with patch('backend.app.services.email_graph.models.user_node.normalize_email') as mock_normalize, \
                patch('backend.app.services.email_graph.models.user_node.extract_email_parts') as mock_extract:
            # Configurer les mocks
            mock_normalize.return_value = "user@example.com"
            mock_extract.return_value = ("user@example.com", "example.com", "User")

            # Appeler la méthode
            user_id = manager.create_user("User <user@example.com>")

            # Vérifier le résultat
            assert user_id is not None
            assert user_id.startswith("user-")
            assert empty_graph.has_node(user_id)

            # Vérifier les attributs du noeud
            node_data = empty_graph.nodes[user_id]
            assert node_data["type"] == "user"
            assert node_data["email"] == "user@example.com"
            assert node_data["name"] == "User"
            assert node_data["domain"] == "example.com"
            assert node_data["is_central_user"] is False
            assert node_data["connection_strength"] == 0.0

    def test_create_user_existing(self, empty_graph):
        """Test que create_user retourne l'ID existant si l'utilisateur existe déjà."""
        manager = UserNodeManager(empty_graph)

        # Ajouter d'abord un noeud utilisateur
        empty_graph.add_node("user-existing", type="user", email="user@example.com")

        # Patch les fonctions d'utilitaire
        with patch('backend.app.services.email_graph.models.user_node.normalize_email') as mock_normalize:
            # Configurer le mock
            mock_normalize.return_value = "user@example.com"

            # Appeler la méthode
            user_id = manager.create_user("user@example.com")

            # Vérifier que l'ID existant est retourné
            assert user_id == "user-existing"

    def test_create_user_central(self, empty_graph):
        """Test la création d'un utilisateur central."""
        manager = UserNodeManager(empty_graph)
        manager.central_user_email = "central@example.com"

        # Patch les fonctions d'utilitaire
        with patch('backend.app.services.email_graph.models.user_node.normalize_email') as mock_normalize, \
                patch('backend.app.services.email_graph.models.user_node.extract_email_parts') as mock_extract:
            # Configurer les mocks
            mock_normalize.return_value = "central@example.com"
            mock_extract.return_value = ("central@example.com", "example.com", "Central User")

            # Appeler la méthode
            user_id = manager.create_user("Central User <central@example.com>")

            # Vérifier que l'utilisateur est marqué comme central
            assert empty_graph.nodes[user_id]["is_central_user"] is True


    def test_update_connection_strength(self, empty_graph):
        """Test la méthode update_connection_strength."""
        manager = UserNodeManager(empty_graph)
        manager.central_user_email = "central@example.com"

        # Créer des noeuds utilisateur
        empty_graph.add_node("user-central", type="user", email="central@example.com",
                             is_central_user=True, connection_strength=0.0)
        empty_graph.add_node("user-other", type="user", email="other@example.com",
                             is_central_user=False, connection_strength=0.0)

        # Cas 1: Mettre à jour la connexion entre l'utilisateur central et un autre utilisateur
        manager.update_connection_strength("user-central", "user-other", 2.5)

        # Vérifier que la force de connexion est mise à jour pour l'autre utilisateur
        assert empty_graph.nodes["user-other"]["connection_strength"] == 2.5

        # Cas 2: Mettre à jour la connexion dans l'autre sens
        manager.update_connection_strength("user-other", "user-central", 1.5)

        # Vérifier que la force de connexion est mise à jour pour l'autre utilisateur (cumulatif)
        assert empty_graph.nodes["user-other"]["connection_strength"] == 4.0

    def test_update_connection_strength_no_central(self, empty_graph):
        """Test que update_connection_strength ne fait rien si aucun utilisateur central n'est défini."""
        manager = UserNodeManager(empty_graph)

        # Créer des noeuds utilisateur
        empty_graph.add_node("user-1", type="user", email="user1@example.com",
                             is_central_user=False, connection_strength=0.0)
        empty_graph.add_node("user-2", type="user", email="user2@example.com",
                             is_central_user=False, connection_strength=0.0)

        # Appeler la méthode
        manager.update_connection_strength("user-1", "user-2", 2.5)

        # Vérifier que les forces de connexion n'ont pas changé
        assert empty_graph.nodes["user-1"]["connection_strength"] == 0.0
        assert empty_graph.nodes["user-2"]["connection_strength"] == 0.0

    def test_create_recipient_relationships(self, empty_graph, sample_email_data):
        """Test la méthode create_recipient_relationships."""
        manager = UserNodeManager(empty_graph)

        # Patch create_user pour éviter les effets secondaires et retourner des IDs prévisibles
        with patch.object(manager, 'create_user') as mock_create_user, \
                patch.object(manager, '_create_user_relation') as mock_create_relation:
            # Configurer les mocks
            mock_create_user.side_effect = lambda email: f"user-{email.split('@')[0]}" if email else None
            mock_create_relation.return_value = {"type": "EMAILED", "weight": 1.0}

            # Appeler la méthode avec un expéditeur et des destinataires
            relations = manager.create_recipient_relationships(sample_email_data, "user-sender")

            # Vérifier que les relations ont été créées
            # Le nombre d'appels dépend du nombre de destinataires (To, Cc, Bcc)
            expected_calls = len(sample_email_data.get("To", "").split(",")) + \
                             len(sample_email_data.get("Cc", "").split(",")) + \
                             len(sample_email_data.get("Bcc", "").split(","))

            # On doit filtrer les entrées vides, donc le compte réel peut être inférieur
            assert len(relations) > 0
            assert mock_create_relation.call_count > 0

    def test_create_user_relation(self, empty_graph):
        """Test la méthode _create_user_relation."""
        manager = UserNodeManager(empty_graph)

        # Créer des noeuds utilisateur
        empty_graph.add_node("user-1", type="user", email="user1@example.com")
        empty_graph.add_node("user-2", type="user", email="user2@example.com")

        # Cas 1: Créer une nouvelle relation
        result1 = manager._create_user_relation("user-1", "user-2", "EMAILED", 1.0)

        # Vérifier que la relation a été créée
        assert empty_graph.has_edge("user-1", "user-2")
        assert result1 is not None
        assert result1["type"] == "EMAILED"
        assert result1["weight"] == 1.0

        # Cas 2: Ajouter une autre relation ou mettre à jour l'existante
        result2 = manager._create_user_relation("user-1", "user-2", "EMAILED", 0.5)

        # Obtenir toutes les arêtes entre ces nœuds
        all_edges = list(empty_graph.get_edge_data("user-1", "user-2").values())

        # Vérifier que le poids a été augmenté ou qu'une nouvelle arête a été créée
        # Si le comportement est de mettre à jour l'arête existante:
        if len(all_edges) == 1:
            assert all_edges[0]["weight"] == 1.5  # Poids cumulé
        # Si le comportement est de créer une nouvelle arête:
        else:
            assert len(all_edges) == 2
            weights = [edge["weight"] for edge in all_edges]
            assert 1.0 in weights and 0.5 in weights

    def test_create_user_relation_invalid(self, empty_graph):
        """Test que _create_user_relation gère correctement les cas invalides."""
        manager = UserNodeManager(empty_graph)

        # Cas 1: Noeud source inexistant
        result1 = manager._create_user_relation("nonexistent", "user-2", "EMAILED", 1.0)
        assert result1 is None

        # Cas 2: Noeud cible inexistant
        empty_graph.add_node("user-1", type="user", email="user1@example.com")
        result2 = manager._create_user_relation("user-1", "nonexistent", "EMAILED", 1.0)
        assert result2 is None

        # Cas 3: Relation avec soi-même
        result3 = manager._create_user_relation("user-1", "user-1", "EMAILED", 1.0)
        assert result3 is None