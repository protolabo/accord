import pytest
import json
import networkx as nx
from unittest.mock import patch, MagicMock
from backend.app.services.email_graph.processor import EmailGraphProcessor


class TestEmailGraphProcessor:
    """Tests pour la classe EmailGraphProcessor."""

    def test_init(self):
        """Test l'initialisation du processeur."""
        processor = EmailGraphProcessor()

        # Vérifier que les attributs importants sont initialisés
        assert isinstance(processor.graph, nx.MultiDiGraph)
        assert processor.central_user_email is None
        assert hasattr(processor, 'message_manager')
        assert hasattr(processor, 'user_manager')
        assert hasattr(processor, 'thread_manager')
        assert hasattr(processor, 'metrics_analyzer')
        assert hasattr(processor, 'network_extractor')

    def test_process_graph_valid_input_string(self, sample_message_json):
        """Test que process_graph fonctionne avec une entrée JSON valide sous forme de chaîne."""
        processor = EmailGraphProcessor()

        # Patch les méthodes internes pour éviter de construire réellement le graphe
        with patch.object(processor, '_build_graph'), \
                patch.object(processor, '_analyze_graph') as mock_analyze:
            # Configurer le mock d'analyse pour renvoyer un résultat simple
            mock_analyze.return_value = {"test": "result"}

            # Configurer le mock pour calculate_stats
            processor.metrics_analyzer.calculate_stats = MagicMock(return_value={"node_count": 10})

            # Appeler la méthode
            result = processor.process_graph(sample_message_json)

            # Vérifier que le résultat est un JSON valide avec les données attendues
            result_dict = json.loads(result)
            assert result_dict["test"] == "result"
            assert result_dict["stats"] == {"node_count": 10}
            assert "metadata" in result_dict
            assert "emails_processed" in result_dict["metadata"]
            assert result_dict["metadata"]["central_user"] == "test.sender@example.com"

    def test_process_graph_valid_input_dict(self):
        """Test que process_graph fonctionne avec une entrée sous forme de dictionnaire."""
        processor = EmailGraphProcessor()

        # Créer un dictionnaire d'entrée
        input_dict = {
            "mails": [{"Message-ID": "test1", "From": "test@example.com"}],
            "central_user": "test@example.com",
            "max_emails": 100
        }

        # Patch les méthodes internes
        with patch.object(processor, '_build_graph'), \
                patch.object(processor, '_analyze_graph') as mock_analyze:
            mock_analyze.return_value = {"test": "result"}
            processor.metrics_analyzer.calculate_stats = MagicMock(return_value={})

            # Appeler la méthode avec un dict au lieu d'une chaîne JSON
            result = processor.process_graph(input_dict)

            # Vérifier que le résultat est un JSON valide
            result_dict = json.loads(result)
            assert "test" in result_dict
            assert "metadata" in result_dict

    def test_process_graph_error_handling(self):
        """Test que process_graph gère correctement les erreurs."""
        processor = EmailGraphProcessor()

        # Patch _build_graph pour simuler une exception
        with patch.object(processor, '_build_graph', side_effect=ValueError("Test error")):
            # Appeler la méthode avec une entrée valide
            result = processor.process_graph('{"mails": []}')

            # Vérifier que le résultat est un JSON d'erreur valide
            result_dict = json.loads(result)
            assert result_dict["status"] == "error"
            assert result_dict["type"] == "ValueError"
            assert "Test error" in result_dict["message"]

    def test_build_graph(self, multiple_emails_data):
        """Test la méthode _build_graph."""
        processor = EmailGraphProcessor()

        # Patch les gestionnaires pour éviter les effets secondaires
        with patch.object(processor, '_process_email') as mock_process:
            # Configurer le mock pour indiquer le succès
            mock_process.return_value = True

            # Appeler la méthode
            processor._build_graph(multiple_emails_data)

            # Vérifier que _process_email a été appelé pour chaque email
            assert mock_process.call_count == len(multiple_emails_data)

    def test_process_email(self, sample_email_data):
        """Test la méthode _process_email."""
        processor = EmailGraphProcessor()

        # Patch les gestionnaires pour éviter les effets secondaires
        with patch.object(processor.message_manager, 'create_message', return_value="msg123"), \
                patch.object(processor.thread_manager, 'create_thread', return_value="thread456"), \
                patch.object(processor.user_manager, 'create_user', return_value="user-1"), \
                patch.object(processor.user_manager, 'create_recipient_relationships', return_value=[]):
            # Appeler la méthode
            result = processor._process_email(sample_email_data)

            # Vérifier que le traitement a réussi
            assert result is True

            # Vérifier que les relations ont été ajoutées au graphe
            # On devrait avoir au moins une relation msg-thread et au moins une relation user-msg
            edges = list(processor.graph.edges(data=True))
            assert any(e[0] == "msg123" and e[1] == "thread456" for e in edges)
            assert any(e[0] == "user-1" and e[1] == "msg123" for e in edges)

    def test_process_email_missing_message_id(self):
        """Test que _process_email gère correctement l'absence de Message-ID."""
        processor = EmailGraphProcessor()

        # Créer un email sans Message-ID
        invalid_email = {"From": "test@example.com", "To": "recipient@example.com"}

        # Appeler la méthode
        result = processor._process_email(invalid_email)

        # Vérifier que le traitement a échoué gracieusement
        assert result is False

    def test_analyze_graph(self):
        """Test la méthode _analyze_graph."""
        processor = EmailGraphProcessor()
        processor.central_user_email = "test@example.com"

        # Patch les analyseurs
        processor.metrics_analyzer.get_top_contacts = MagicMock(return_value=["contact1", "contact2"])
        processor.metrics_analyzer.get_top_threads = MagicMock(return_value=["thread1", "thread2"])
        processor.network_extractor.extract_communication_network = MagicMock(return_value={"nodes": [], "links": []})

        # Appeler la méthode
        result = processor._analyze_graph()

        # Vérifier le résultat
        assert result["central_user"] == "test@example.com"
        assert result["top_contacts"] == ["contact1", "contact2"]
        assert result["top_threads"] == ["thread1", "thread2"]
        assert "communication_network" in result

    def test_integration_small_dataset(self, multiple_emails_data):
        """Test d'intégration avec un petit jeu de données."""
        processor = EmailGraphProcessor()

        # Créer un message au format attendu
        message = {
            "mails": multiple_emails_data[:3],  # Limitez à 3 emails pour le test
            "central_user": "user0@example.com",
            "max_emails": 5
        }

        # Traiter le message
        result = processor.process_graph(message)

        # Vérifier que le résultat est un JSON valide
        result_dict = json.loads(result)

        # Vérifier la présence des clés attendues
        assert "stats" in result_dict
        assert "metadata" in result_dict
        assert "top_contacts" in result_dict
        assert "top_threads" in result_dict
        assert "communication_network" in result_dict

        # Vérifier les métadonnées
        assert result_dict["metadata"]["emails_processed"] == 3
        assert result_dict["metadata"]["central_user"] == "user0@example.com"