import pytest
from backend.app.services.email_graph.analysis.network_extraction import NetworkExtractor


class TestNetworkExtractor:
    """Tests pour la classe NetworkExtractor."""

    def test_init(self, empty_graph):
        """Test l'initialisation de l'extracteur."""
        extractor = NetworkExtractor(empty_graph)
        assert extractor.graph == empty_graph

    def test_set_graph(self, empty_graph):
        """Test la méthode set_graph."""
        extractor = NetworkExtractor(None)
        extractor.set_graph(empty_graph)
        assert extractor.graph == empty_graph

    def test_extract_communication_network_empty(self, empty_graph):
        """Test extract_communication_network sur un graphe vide."""
        extractor = NetworkExtractor(empty_graph)
        result = extractor.extract_communication_network()

        # Vérifier le format de base
        assert "nodes" in result
        assert "links" in result
        assert result["nodes"] == []
        assert result["links"] == []

    def test_extract_communication_network(self, populated_graph):
        """Test extract_communication_network avec un graphe peuplé."""
        extractor = NetworkExtractor(populated_graph)

        # Ajouter des noeuds utilisateur supplémentaires
        populated_graph.add_node(
            "user-3",
            type="user",
            email="user3@example.com",
            name="User Three",
            domain="example.com",
            is_central_user=False,
            connection_strength=5.0
        )

        # Ajouter des relations entre utilisateurs
        populated_graph.add_edge(
            "user-1",
            "user-2",
            type="EMAILED",
            weight=2.0
        )

        populated_graph.add_edge(
            "user-2",
            "user-3",
            type="EMAILED_CC",
            weight=1.5
        )

        populated_graph.add_edge(
            "user-3",
            "user-1",
            type="EMAILED_BCC",
            weight=0.5
        )

        # Ajouter une relation non-pertinente
        populated_graph.add_edge(
            "user-1",
            "msg-1",
            type="SENT",
            weight=1.0
        )

        # Appeler la méthode
        result = extractor.extract_communication_network()

        # Vérifier les noeuds
        assert "nodes" in result
        assert len(result["nodes"]) == 3  # Tous les utilisateurs

        # Vérifier que chaque noeud a les attributs attendus
        for node in result["nodes"]:
            assert "id" in node
            assert "email" in node
            assert "name" in node
            assert "is_central" in node
            assert "connection_strength" in node

        # Vérifier les liens
        assert "links" in result
        assert len(result["links"]) == 3  # Toutes les relations d'email entre utilisateurs

        # Vérifier que chaque lien a les attributs attendus
        for link in result["links"]:
            assert "source" in link
            assert "target" in link
            assert "type" in link
            assert "weight" in link

            # Vérifier que ce sont des relations d'email
            assert link["type"] in ["EMAILED", "EMAILED_CC", "EMAILED_BCC"]

            # Vérifier que les liens connectent des utilisateurs existants
            assert link["source"] in ["user-1", "user-2", "user-3"]
            assert link["target"] in ["user-1", "user-2", "user-3"]

    def test_extract_communication_network_filters_non_user_nodes(self, populated_graph):
        """Test que extract_communication_network filtre les noeuds non-utilisateur."""
        extractor = NetworkExtractor(populated_graph)

        # Ajouter une relation non-utilisateur (message-message)
        populated_graph.add_edge(
            "msg-1",
            "msg-2",
            type="RELATED_TO",
            weight=1.0
        )

        # Appeler la méthode
        result = extractor.extract_communication_network()

        # Vérifier que les noeuds message ne sont pas inclus
        for node in result["nodes"]:
            assert node["id"].startswith("user-")

        # Vérifier que les relations message-message ne sont pas incluses
        for link in result["links"]:
            assert not (link["source"].startswith("msg-") and link["target"].startswith("msg-"))

    def test_extract_communication_network_filters_non_email_edges(self, populated_graph):
        """Test que extract_communication_network filtre les relations non-email."""
        extractor = NetworkExtractor(populated_graph)

        # Ajouter une relation utilisateur-utilisateur d'un type non-email
        populated_graph.add_edge(
            "user-1",
            "user-2",
            type="KNOWS",
            weight=1.0
        )

        # Appeler la méthode
        result = extractor.extract_communication_network()

        # Vérifier que la relation KNOWS n'est pas incluse
        for link in result["links"]:
            assert link["type"] != "KNOWS"
            assert link["type"] in ["EMAILED", "EMAILED_CC", "EMAILED_BCC"]