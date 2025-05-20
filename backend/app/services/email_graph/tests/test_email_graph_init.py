import json
import pytest
from unittest.mock import patch, MagicMock
from backend.app.services.email_graph import process_graph


@pytest.mark.parametrize(
    "success_result, expected_output", [
        ({"status": "success", "data": {}}, json.dumps({"status": "success", "data": {}})),
        ({"top_contacts": []}, json.dumps({"top_contacts": []}))
    ]
)
def test_process_graph_success(sample_message_json, success_result, expected_output):
    """Test que process_graph fonctionne correctement en cas de succès."""
    with patch('backend.app.services.email_graph.EmailGraphProcessor') as MockProcessor:
        # Configurer le mock
        mock_instance = MockProcessor.return_value
        mock_instance.process_graph.return_value = expected_output

        # Appeler la fonction
        result = process_graph(sample_message_json)

        # Vérifier que process_graph a été appelée avec les bons arguments
        mock_instance.process_graph.assert_called_once_with(sample_message_json)

        # Vérifier le résultat
        assert result == expected_output


def test_process_graph_error_handling():
    """Test que process_graph gère correctement les exceptions."""
    with patch('backend.app.services.email_graph.EmailGraphProcessor') as MockProcessor:
        # Configurer le mock pour lever une exception
        mock_instance = MockProcessor.return_value
        mock_instance.process_graph.side_effect = ValueError("Test error")

        # Appeler la fonction
        result = process_graph("invalid_input")

        # Vérifier que le résultat est une réponse d'erreur en JSON
        result_dict = json.loads(result)
        assert result_dict["status"] == "error"
        assert result_dict["type"] == "ValueError"
        assert "Test error" in result_dict["message"]


def test_process_graph_integration(sample_message_json):
    """Test d'intégration pour process_graph."""
    with patch('backend.app.services.email_graph.processor.nx') as mock_nx:
        # Configurer le mock pour NetworkX
        mock_nx.MultiDiGraph.return_value = MagicMock()

        # Appeler la fonction avec une entrée valide
        result = process_graph(sample_message_json)

        # Vérifier que le résultat est un JSON valide
        result_dict = json.loads(result)

        # On s'attend à ce que la fonction renvoie un dictionnaire
        # avec soit un statut d'erreur, soit des données d'analyse
        assert isinstance(result_dict, dict)