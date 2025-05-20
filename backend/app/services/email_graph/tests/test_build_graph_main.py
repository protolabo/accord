import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from backend.app.services.email_graph.build_graph_main import (
    OptimizedMockDataService,
    main,
    memory_usage_gb,
    log_memory_usage
)


class TestOptimizedMockDataService:
    """Tests pour la classe OptimizedMockDataService."""

    def test_init(self):
        """Test l'initialisation du service."""
        with tempfile.TemporaryDirectory() as mock_dir, tempfile.TemporaryDirectory() as out_dir:
            # Créer des chemins Path
            mock_path = Path(mock_dir)
            out_path = Path(out_dir)

            # Initialiser le service
            service = OptimizedMockDataService(mock_path, out_path)

            # Vérifier les attributs
            assert service.mock_data_dir == mock_path
            assert service.output_dir == out_path

    def test_init_with_string_paths(self):
        """Test l'initialisation avec des chemins de type chaîne."""
        with tempfile.TemporaryDirectory() as mock_dir, tempfile.TemporaryDirectory() as out_dir:
            # Initialiser le service avec des chaînes
            service = OptimizedMockDataService(mock_dir, out_dir)

            # Vérifier que les chemins sont convertis en Path
            assert isinstance(service.mock_data_dir, Path)
            assert isinstance(service.output_dir, Path)
            assert str(service.mock_data_dir) == mock_dir
            assert str(service.output_dir) == out_dir

    def test_init_creates_output_dir(self):
        """Test que le répertoire de sortie est créé s'il n'existe pas."""
        with tempfile.TemporaryDirectory() as mock_dir:
            # Créer un chemin de sortie qui n'existe pas
            out_dir = os.path.join(mock_dir, "non_existent_output")

            # Vérifier que le répertoire n'existe pas
            assert not os.path.exists(out_dir)

            # Initialiser le service
            service = OptimizedMockDataService(mock_dir, out_dir)

            # Vérifier que le répertoire a été créé
            assert os.path.exists(out_dir)

    def test_init_invalid_mock_dir(self):
        """Test que l'initialisation échoue si le répertoire de données n'existe pas."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Créer un chemin qui n'existe pas
            non_existent_dir = os.path.join(temp_dir, "non_existent_mock")

            # Vérifier que l'initialisation lève une exception
            with pytest.raises(ValueError):
                OptimizedMockDataService(non_existent_dir, temp_dir)

    def test_get_all_email_batches_empty(self):
        """Test get_all_email_batches lorsque le répertoire est vide."""
        with tempfile.TemporaryDirectory() as mock_dir, tempfile.TemporaryDirectory() as out_dir:
            service = OptimizedMockDataService(mock_dir, out_dir)

            # Appeler la méthode
            result = service.get_all_email_batches()

            # Vérifier le résultat
            assert result == []

    def test_get_all_email_batches(self):
        """Test get_all_email_batches avec des fichiers de données."""
        with tempfile.TemporaryDirectory() as mock_dir, tempfile.TemporaryDirectory() as out_dir:
            # Créer quelques fichiers JSON de test
            batch1 = [{"Message-ID": "msg1", "From": "user1@example.com"}]
            batch2 = [{"Message-ID": "msg2", "From": "user2@example.com"}]

            with open(os.path.join(mock_dir, "batch1.json"), "w") as f:
                json.dump(batch1, f)

            with open(os.path.join(mock_dir, "batch2.json"), "w") as f:
                json.dump(batch2, f)

            # Initialiser le service
            service = OptimizedMockDataService(mock_dir, out_dir)

            # Appeler la méthode
            result = service.get_all_email_batches()

            # Vérifier le résultat
            assert len(result) == 2
            assert result[0]["Message-ID"] == "msg1"
            assert result[1]["Message-ID"] == "msg2"

    def test_get_all_email_batches_max_emails(self):
        """Test get_all_email_batches avec une limite de emails."""
        with tempfile.TemporaryDirectory() as mock_dir, tempfile.TemporaryDirectory() as out_dir:
            # Créer quelques fichiers JSON de test avec plusieurs emails
            batch1 = [{"Message-ID": f"msg{i}", "From": f"user{i}@example.com"} for i in range(5)]
            batch2 = [{"Message-ID": f"msg{i + 5}", "From": f"user{i + 5}@example.com"} for i in range(5)]

            with open(os.path.join(mock_dir, "batch1.json"), "w") as f:
                json.dump(batch1, f)

            with open(os.path.join(mock_dir, "batch2.json"), "w") as f:
                json.dump(batch2, f)

            # Initialiser le service
            service = OptimizedMockDataService(mock_dir, out_dir)

            # Appeler la méthode avec une limite
            result = service.get_all_email_batches(max_emails=3)

            # Vérifier le résultat
            assert len(result) == 3
            assert result[0]["Message-ID"] == "msg0"
            assert result[1]["Message-ID"] == "msg1"
            assert result[2]["Message-ID"] == "msg2"

    def test_get_all_email_batches_error_handling(self):
        """Test que get_all_email_batches gère les erreurs de lecture."""
        with tempfile.TemporaryDirectory() as mock_dir, tempfile.TemporaryDirectory() as out_dir:
            # Créer un fichier JSON valide
            batch1 = [{"Message-ID": "msg1", "From": "user1@example.com"}]
            with open(os.path.join(mock_dir, "batch1.json"), "w") as f:
                json.dump(batch1, f)

            # Créer un fichier JSON invalide
            with open(os.path.join(mock_dir, "invalid.json"), "w") as f:
                f.write("This is not valid JSON")

            # Initialiser le service
            service = OptimizedMockDataService(mock_dir, out_dir)

            # Appeler la méthode
            result = service.get_all_email_batches()

            # Vérifier que les emails valides sont retournés
            assert len(result) == 1
            assert result[0]["Message-ID"] == "msg1"


class TestBuildGraphMain:
    """Tests pour les fonctions principales du module build_graph_main."""

    def test_memory_usage_gb(self):
        """Test la fonction memory_usage_gb."""
        with patch('psutil.Process') as mock_process:
            # Configurer le mock
            mock_instance = mock_process.return_value
            mock_instance.memory_info.return_value.rss = 1024 * 1024 * 1024  # 1 GB en octets

            # Appeler la fonction
            result = memory_usage_gb()

            # Vérifier le résultat
            assert round(result, 2) == 1.0

    def test_log_memory_usage(self, capsys):
        """Test la fonction log_memory_usage."""
        with patch('backend.app.services.email_graph.build_graph_main.memory_usage_gb') as mock_memory:
            # Configurer le mock
            mock_memory.return_value = 2.5

            # Appeler la fonction
            log_memory_usage("test label")

            # Vérifier la sortie
            captured = capsys.readouterr()
            assert "Memory usage (test label): 2.50 GB" in captured.out


    def test_main_with_directory_input(self):
        """Test la fonction main avec un répertoire en entrée."""
        with tempfile.TemporaryDirectory() as input_dir, \
                tempfile.TemporaryDirectory() as output_dir, \
                patch('backend.app.services.email_graph.build_graph_main.EmailGraphProcessor') as MockProcessor, \
                patch('backend.app.services.email_graph.build_graph_main.OptimizedMockDataService') as MockService:
            # Configurer les mocks
            mock_processor = MockProcessor.return_value
            mock_processor.process_graph.return_value = json.dumps({"status": "success"})

            mock_service = MockService.return_value
            mock_service.get_all_email_batches.return_value = [{"Message-ID": "msg1", "From": "user1@example.com"}]

            # Appeler la fonction
            main(input_dir=input_dir, output_dir=output_dir, central_user="user1@example.com", max_emails=100)

            # Vérifier que le service a été appelé
            MockService.assert_called_once_with(Path(input_dir), output_dir)
            mock_service.get_all_email_batches.assert_called_once_with(max_emails=100)

            # Vérifier que process_graph a été appelé
            mock_processor.process_graph.assert_called_once()

            # Vérifier que le fichier de résultat a été créé
            result_file = os.path.join(output_dir, "email_graph_results.json")
            assert os.path.exists(result_file)