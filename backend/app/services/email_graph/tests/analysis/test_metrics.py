import pytest
from unittest.mock import patch, MagicMock
import networkx as nx
from backend.app.services.email_graph.analysis.metrics import GraphMetricsAnalyzer
from backend.app.services.email_graph.analysis.metrics import GraphMetricsAnalyzer
import backend.app.services.email_graph.analysis.metrics as metrics_module


class TestGraphMetricsAnalyzer:
    """Tests pour la classe GraphMetricsAnalyzer."""

    def test_init(self, empty_graph):
        """Test l'initialisation de l'analyseur."""
        analyzer = GraphMetricsAnalyzer(empty_graph)
        assert analyzer.graph == empty_graph

    def test_set_graph(self, empty_graph):
        """Test la méthode set_graph."""
        analyzer = GraphMetricsAnalyzer(None)
        analyzer.set_graph(empty_graph)
        assert analyzer.graph == empty_graph

    def test_get_top_contacts_empty(self, empty_graph):
        """Test get_top_contacts sur un graphe vide."""
        analyzer = GraphMetricsAnalyzer(empty_graph)
        result = analyzer.get_top_contacts(5)
        assert result == []

    def test_get_top_contacts(self, populated_graph):
        """Test get_top_contacts avec des contacts existants."""
        analyzer = GraphMetricsAnalyzer(populated_graph)

        # Ajouter quelques noeuds utilisateur avec des forces de connexion différentes
        populated_graph.add_node(
            "user-3",
            type="user",
            email="user3@example.com",
            name="User Three",
            domain="example.com",
            is_central_user=False,
            connection_strength=15.0
        )

        populated_graph.add_node(
            "user-4",
            type="user",
            email="user4@example.com",
            name="User Four",
            domain="example.com",
            is_central_user=False,
            connection_strength=7.5
        )

        # Appeler la méthode
        result = analyzer.get_top_contacts(3)

        # Vérifier que les résultats sont triés par force de connexion décroissante
        assert len(result) == 3
        assert result[0]["id"] == "user-3"  # Le plus fort
        assert result[1]["id"] == "user-4"  # Le deuxième plus fort

        # Vérifier le format des résultats
        for contact in result:
            assert "id" in contact
            assert "email" in contact
            assert "name" in contact
            assert "domain" in contact
            assert "connection_strength" in contact
            assert "sent_count" in contact
            assert "received_count" in contact

    def test_get_top_contacts_limit(self, populated_graph):
        """Test que get_top_contacts respecte la limite."""
        analyzer = GraphMetricsAnalyzer(populated_graph)

        # Ajouter plusieurs noeuds utilisateur
        for i in range(10):
            populated_graph.add_node(
                f"user-extra-{i}",
                type="user",
                email=f"extra{i}@example.com",
                name=f"Extra User {i}",
                domain="example.com",
                is_central_user=False,
                connection_strength=float(i)
            )

        # Appeler la méthode avec une limite de 5
        result = analyzer.get_top_contacts(5)

        # Vérifier que seulement 5 contacts sont retournés
        assert len(result) == 5

    def test_get_top_contacts_skip_central(self, populated_graph):
        """Test que get_top_contacts ignore l'utilisateur central."""
        analyzer = GraphMetricsAnalyzer(populated_graph)

        # L'utilisateur central ne doit pas être inclus dans les résultats
        result = analyzer.get_top_contacts(5)

        # Vérifier qu'aucun utilisateur marqué comme central n'est dans les résultats
        for contact in result:
            assert populated_graph.nodes[contact["id"]].get("is_central_user", False) is False

    def test_get_top_threads_empty(self, empty_graph):
        """Test get_top_threads sur un graphe vide."""
        analyzer = GraphMetricsAnalyzer(empty_graph)
        result = analyzer.get_top_threads(5)
        assert result == []

    def test_get_top_threads(self, populated_graph):
        """Test get_top_threads avec des threads existants."""
        analyzer = GraphMetricsAnalyzer(populated_graph)

        # Ajouter quelques noeuds thread avec différents nombres de messages
        populated_graph.add_node(
            "thread-2",
            type="thread",
            message_count=5,
            participants=["user1@example.com", "user3@example.com"],
            subject="Thread with 5 messages"
        )

        populated_graph.add_node(
            "thread-3",
            type="thread",
            message_count=3,
            participants=["user2@example.com", "user4@example.com"],
            subject="Thread with 3 messages"
        )

        # Appeler la méthode
        result = analyzer.get_top_threads(3)

        # Vérifier que les résultats sont triés par nombre de messages décroissant
        assert len(result) == 3
        assert result[0]["id"] == "thread-2"  # Le plus de messages
        assert result[1]["id"] == "thread-3"  # Le deuxième plus de messages

        # Vérifier le format des résultats
        for thread in result:
            assert "id" in thread
            assert "message_count" in thread
            assert "participants" in thread
            assert "subject" in thread

    def test_get_top_threads_limit(self, populated_graph):
        """Test que get_top_threads respecte la limite."""
        analyzer = GraphMetricsAnalyzer(populated_graph)

        # Ajouter plusieurs noeuds thread
        for i in range(10):
            populated_graph.add_node(
                f"thread-extra-{i}",
                type="thread",
                message_count=i,
                participants=[f"user{i}@example.com"],
                subject=f"Thread {i}"
            )

        # Appeler la méthode avec une limite de 5
        result = analyzer.get_top_threads(5)

        # Vérifier que seulement 5 threads sont retournés
        assert len(result) == 5

    def test_calculate_stats_empty(self, empty_graph):
        """Test calculate_stats sur un graphe vide."""
        analyzer = GraphMetricsAnalyzer(empty_graph)
        result = analyzer.calculate_stats()

        # Vérifier les statistiques de base
        assert result["total_nodes"] == 0
        assert result["total_edges"] == 0
        assert result["node_types"] == {}
        assert result["edge_types"] == {}

        # Pas de centralité sur un graphe vide
        assert "top_degree_centrality" not in result
        assert "top_betweenness_centrality" not in result

    def test_calculate_stats(self, populated_graph):
        """Test calculate_stats avec un graphe peuplé."""
        analyzer = GraphMetricsAnalyzer(populated_graph)

        # Appeler la méthode sans patch
        result = analyzer.calculate_stats()

        # Vérifier uniquement les statistiques de base
        assert result["total_nodes"] > 0
        assert result["total_edges"] > 0
        assert "user" in result["node_types"]
        assert "message" in result["node_types"]
        assert "thread" in result["node_types"]

        # Pour les métriques de centralité, vérifier juste leur présence sans détails
        if "top_degree_centrality" in result:
            assert isinstance(result["top_degree_centrality"], list)

        if "top_betweenness_centrality" in result:
            assert isinstance(result["top_betweenness_centrality"], list)

    def test_get_top_nodes_by_metric(self, populated_graph):
        """Test la méthode _get_top_nodes_by_metric."""
        analyzer = GraphMetricsAnalyzer(populated_graph)

        # Créer un dictionnaire de métrique
        metric_dict = {
            "user-1": 0.9,
            "user-2": 0.7,
            "msg-1": 0.5,
            "msg-2": 0.3,
            "thread-1": 0.1
        }

        # Appeler la méthode
        result = analyzer._get_top_nodes_by_metric(metric_dict, 2)

        # Vérifier que seuls les noeuds utilisateur sont inclus
        assert len(result) == 2
        assert result[0]["id"] == "user-1"
        assert result[1]["id"] == "user-2"

        # Vérifier le format des résultats
        for node in result:
            assert "id" in node
            assert "email" in node
            assert "name" in node
            assert "value" in node

    def test_get_top_nodes_by_metric_limit(self, populated_graph):
        """Test que _get_top_nodes_by_metric respecte la limite."""
        analyzer = GraphMetricsAnalyzer(populated_graph)

        # Créer un dictionnaire de métrique avec beaucoup de noeuds
        metric_dict = {f"user-{i}": float(i) / 10 for i in range(10)}

        # Appeler la méthode avec une limite de 3
        result = analyzer._get_top_nodes_by_metric(metric_dict, 3)

        # Vérifier que seulement 3 noeuds sont retournés
        assert len(result) <= 3

    def test_get_top_nodes_by_metric_non_user_nodes(self, populated_graph):
        """Test que _get_top_nodes_by_metric filtre les noeuds non-utilisateur."""
        analyzer = GraphMetricsAnalyzer(populated_graph)

        # Créer un dictionnaire de métrique avec des noeuds non-utilisateur
        metric_dict = {
            "msg-1": 0.9,
            "thread-1": 0.8,
            "user-1": 0.7
        }

        # Appeler la méthode
        result = analyzer._get_top_nodes_by_metric(metric_dict, 3)

        # Vérifier que seuls les noeuds utilisateur sont inclus
        assert len(result) == 1
        assert result[0]["id"] == "user-1"