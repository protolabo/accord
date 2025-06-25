import pytest
from unittest.mock import patch
from datetime import datetime
from backend.app.services.email_graph.models.message_node import MessageNodeManager


class TestMessageNodeManager:
    """Tests pour la classe MessageNodeManager."""

    def test_init(self, empty_graph):
        """Test l'initialisation du gestionnaire."""
        manager = MessageNodeManager(empty_graph)
        assert manager.graph == empty_graph

    def test_set_graph(self, empty_graph):
        """Test la méthode set_graph."""
        manager = MessageNodeManager(None)
        manager.set_graph(empty_graph)
        assert manager.graph == empty_graph

    def test_create_message_basic(self, empty_graph, sample_email_data):
        """Test la création d'un noeud message avec des données de base."""
        manager = MessageNodeManager(empty_graph)

        # Appeler la méthode
        message_id = manager.create_message(sample_email_data)

        # Vérifier le résultat
        assert message_id == sample_email_data["Message-ID"]
        assert empty_graph.has_node(message_id)

        # Vérifier que les attributs sont correctement définis
        node_data = empty_graph.nodes[message_id]
        assert node_data["type"] == "message"
        assert node_data["thread_id"] == sample_email_data["Thread-ID"]
        assert node_data["from_email"] is not None
        assert len(node_data["to"]) == 2  # Deux destinataires
        assert len(node_data["cc"]) == 2  # Deux destinataires en CC
        assert len(node_data["bcc"]) == 1  # Un destinataire en BCC
        assert node_data["subject"] == sample_email_data["Subject"]

    def test_create_message_existing_node(self, empty_graph, sample_email_data):
        """Test que create_message retourne l'ID existant si le noeud existe déjà."""
        manager = MessageNodeManager(empty_graph)

        # Ajouter d'abord le noeud
        message_id = sample_email_data["Message-ID"]
        empty_graph.add_node(message_id, type="message", existing=True)

        # Appeler la méthode
        result = manager.create_message(sample_email_data)

        # Vérifier que l'ID existant est retourné
        assert result == message_id

        # Vérifier que les attributs n'ont pas été écrasés
        assert empty_graph.nodes[message_id]["existing"] == True

    def test_create_message_missing_message_id(self, empty_graph):
        """Test que create_message lève une exception quand Message-ID est manquant."""
        manager = MessageNodeManager(empty_graph)

        # Créer un email sans Message-ID
        invalid_email = {"From": "test@example.com", "To": "recipient@example.com"}

        # Vérifier que la méthode lève une ValueError
        with pytest.raises(ValueError, match="None cannot be a node"):
            manager.create_message(invalid_email)

    def test_create_message_date_handling(self, empty_graph):
        """Test le traitement des dates dans create_message."""
        manager = MessageNodeManager(empty_graph)

        # Cas 1: Date valide au format ISO
        email_valid_date = {
            "Message-ID": "msg1",
            "Internal-Date": "2023-04-15T14:30:45Z"
        }

        # Cas 2: Date dans un format non-ISO
        email_invalid_date = {
            "Message-ID": "msg2",
            "Internal-Date": "15/04/2023 14:30:45"
        }

        # Cas 3: Date manquante
        email_no_date = {
            "Message-ID": "msg3"
        }

        # Appeler la méthode pour chaque cas
        manager.create_message(email_valid_date)
        manager.create_message(email_invalid_date)
        manager.create_message(email_no_date)

        # Vérifier les résultats
        # Pour la date valide, on attend une date ISO
        assert empty_graph.nodes["msg1"]["date"] != ""
        # Pour la date invalide, on attend une chaîne vide
        assert empty_graph.nodes["msg2"]["date"] == ""
        # Pour aucune date, on attend une chaîne vide
        assert empty_graph.nodes["msg3"]["date"] == ""

    def test_create_message_email_normalization(self, empty_graph):
        """Test la normalisation des emails dans create_message."""
        manager = MessageNodeManager(empty_graph)

        # Créer un email avec différents formats d'adresses
        email_data = {
            "Message-ID": "msg1",
            "From": "Test Sender <sender@example.com>",
            "To": "Recipient 1 <recipient1@example.com>, recipient2@example.com",
            "Cc": " Cc User <cc@example.com> ",
            "Bcc": "Bcc User <bcc@example.com>"
        }

        # Patch la fonction normalize_email
        with patch('backend.app.services.email_graph.models.message_node.normalize_email') as mock_normalize:
            # Configurer le mock pour renvoyer des valeurs normalisées
            mock_normalize.side_effect = lambda email: email.lower().split('<')[-1].split('>')[
                0].strip() if '<' in email else email.lower().strip()

            # Appeler la méthode
            manager.create_message(email_data)

            # Vérifier que normalize_email a été appelé pour chaque adresse
            assert mock_normalize.call_count >= 4  # Au moins 4 appels (From, To x2, Cc, Bcc)

            # Vérifier que les emails normalisés sont stockés
            node_data = empty_graph.nodes["msg1"]
            assert node_data["from_email"] == "sender@example.com"
            assert "recipient1@example.com" in node_data["to"]
            assert "recipient2@example.com" in node_data["to"]
            assert "cc@example.com" in node_data["cc"]
            assert "bcc@example.com" in node_data["bcc"]