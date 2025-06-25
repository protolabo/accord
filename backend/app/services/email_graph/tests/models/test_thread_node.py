import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from backend.app.services.email_graph.models.thread_node import ThreadNodeManager


class TestThreadNodeManager:
    """Tests pour la classe ThreadNodeManager."""

    def test_init(self, empty_graph):
        """Test l'initialisation du gestionnaire."""
        manager = ThreadNodeManager(empty_graph)
        assert manager.graph == empty_graph

    def test_set_graph(self, empty_graph):
        """Test la méthode set_graph."""
        manager = ThreadNodeManager(None)
        manager.set_graph(empty_graph)
        assert manager.graph == empty_graph

    def test_create_thread_new(self, empty_graph, sample_email_data):
        """Test la création d'un nouveau noeud thread."""
        manager = ThreadNodeManager(empty_graph)

        # Appeler la méthode
        thread_id = manager.create_thread(sample_email_data)

        # Vérifier le résultat
        assert thread_id == sample_email_data["Thread-ID"]
        assert empty_graph.has_node(thread_id)

        # Vérifier les attributs du noeud
        node_data = empty_graph.nodes[thread_id]
        assert node_data["type"] == "thread"
        assert node_data["first_message_id"] == sample_email_data["Message-ID"]
        assert node_data["message_count"] == 1
        assert node_data["subject"] == sample_email_data["Subject"]

        # Vérifier que les participants ont été correctement extraits
        assert len(node_data["participants"]) > 0
        assert sample_email_data["From"] in node_data["participants"]
        for recipient in sample_email_data["To"].split(","):
            if recipient.strip():
                assert recipient.strip() in node_data["participants"]

    def test_create_thread_existing(self, empty_graph, sample_email_data):
        """Test la mise à jour d'un thread existant."""
        manager = ThreadNodeManager(empty_graph)

        # Créer d'abord un thread
        thread_id = sample_email_data["Thread-ID"]
        empty_graph.add_node(
            thread_id,
            type="thread",
            first_message_id="old-message-id",
            message_count=1,
            last_message_date="2023-04-14T10:00:00",
            participants=["old-sender@example.com"],
            topics=[],
            subject="Original Subject"
        )

        # Créer un nouvel email avec une date plus récente
        new_email = sample_email_data.copy()
        new_email["Message-ID"] = "new-message-id"
        new_email["Internal-Date"] = datetime.now().isoformat()

        # Appeler la méthode
        result = manager.create_thread(new_email)

        # Vérifier le résultat
        assert result == thread_id

        # Vérifier que les attributs ont été mis à jour
        node_data = empty_graph.nodes[thread_id]
        assert node_data["message_count"] == 2  # Incrémenté
        assert node_data["first_message_id"] == "old-message-id"  # Non modifié
        assert "old-sender@example.com" in node_data["participants"]  # Préservé
        assert new_email["From"] in node_data["participants"]  # Ajouté

        # Vérifier que la date du dernier message a été mise à jour
        assert node_data["last_message_date"] != "2023-04-14T10:00:00"

    def test_create_thread_date_handling(self, empty_graph):
        """Test le traitement des dates dans create_thread."""
        manager = ThreadNodeManager(empty_graph)

        # Cas 1: Email avec une date valide
        email_valid_date = {
            "Message-ID": "msg1",
            "Thread-ID": "thread1",
            "Internal-Date": "2023-04-15T14:30:45Z",
            "From": "sender@example.com"
        }

        # Cas 2: Email avec une date invalide
        email_invalid_date = {
            "Message-ID": "msg2",
            "Thread-ID": "thread2",
            "Internal-Date": "invalid-date",
            "From": "sender@example.com"
        }

        # Cas 3: Email sans date
        email_no_date = {
            "Message-ID": "msg3",
            "Thread-ID": "thread3",
            "From": "sender@example.com"
        }

        # Appeler la méthode pour chaque cas
        thread_id1 = manager.create_thread(email_valid_date)
        thread_id2 = manager.create_thread(email_invalid_date)
        thread_id3 = manager.create_thread(email_no_date)

        # Vérifier les résultats
        # Pour la date valide, on attend une date ISO
        assert empty_graph.nodes[thread_id1]["last_message_date"] != ""
        # Pour la date invalide, on attend une chaîne vide
        assert empty_graph.nodes[thread_id2]["last_message_date"] == ""
        # Pour aucune date, on attend une chaîne vide
        assert empty_graph.nodes[thread_id3]["last_message_date"] == ""

    def test_create_thread_missing_thread_id(self, empty_graph):
        """Test que create_thread retourne None si Thread-ID est manquant."""
        manager = ThreadNodeManager(empty_graph)

        # Créer un email sans Thread-ID
        email_no_thread = {
            "Message-ID": "msg1",
            "From": "sender@example.com"
        }

        # Appeler la méthode
        result = manager.create_thread(email_no_thread)

        # Vérifier le résultat
        assert result is None
        assert empty_graph.number_of_nodes() == 0

    def test_create_thread_participants_update(self, empty_graph):
        """Test la mise à jour des participants dans un thread existant."""
        manager = ThreadNodeManager(empty_graph)

        # Créer d'abord un thread avec certains participants
        thread_id = "thread1"
        empty_graph.add_node(
            thread_id,
            type="thread",
            message_count=1,
            participants=["user1@example.com", "user2@example.com"],
            last_message_date="2023-04-14T10:00:00"
        )

        # Créer un nouvel email avec différents participants
        new_email = {
            "Message-ID": "msg2",
            "Thread-ID": thread_id,
            "Internal-Date": datetime.now().isoformat(),
            "From": "user3@example.com",
            "To": "user1@example.com, user4@example.com",
            "Cc": "user5@example.com"
        }

        # Appeler la méthode
        manager.create_thread(new_email)

        # Vérifier que tous les participants sont inclus
        node_data = empty_graph.nodes[thread_id]
        participants = set(node_data["participants"])

        assert "user1@example.com" in participants  # Existant et aussi destinataire
        assert "user2@example.com" in participants  # Existant
        assert "user3@example.com" in participants  # Nouvel expéditeur
        assert "user4@example.com" in participants  # Nouveau destinataire
        assert "user5@example.com" in participants  # Nouveau CC

    def test_create_thread_date_comparison(self, empty_graph):
        """Test la comparaison des dates pour la mise à jour du dernier message."""
        manager = ThreadNodeManager(empty_graph)

        # Créer un thread avec une date
        thread_id = "thread1"
        earlier_date = (datetime.now() - timedelta(days=1)).isoformat()
        later_date = datetime.now().isoformat()

        empty_graph.add_node(
            thread_id,
            type="thread",
            message_count=1,
            participants=["user1@example.com"],
            last_message_date=earlier_date
        )

        # Cas 1: Email avec une date plus récente
        email_later = {
            "Message-ID": "msg2",
            "Thread-ID": thread_id,
            "Internal-Date": later_date,
            "From": "user2@example.com"
        }

        # Cas 2: Email avec une date plus ancienne
        email_earlier = {
            "Message-ID": "msg3",
            "Thread-ID": thread_id,
            "Internal-Date": (datetime.now() - timedelta(days=2)).isoformat(),
            "From": "user3@example.com"
        }

        # Appeler la méthode pour chaque cas
        manager.create_thread(email_later)

        # Vérifier que la date a été mise à jour
        assert empty_graph.nodes[thread_id]["last_message_date"] == later_date

        # Appeler la méthode pour l'email plus ancien
        manager.create_thread(email_earlier)

        # Vérifier que la date n'a pas été changée
        assert empty_graph.nodes[thread_id]["last_message_date"] == later_date