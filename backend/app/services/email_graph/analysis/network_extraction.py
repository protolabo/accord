"""
Extracteur de réseau de communication pour le graphe d'emails.
"""


class NetworkExtractor:
    """Classe pour l'extraction du réseau de communication."""

    def __init__(self, graph):
        """
        Initialise l'extracteur de réseau

        Args:
            graph: Instance NetworkX du graphe à analyser
        """
        self.graph = graph

    def set_graph(self, graph):
        """
        Met à jour l'instance de graphe

        Args:
            graph: Nouvelle instance NetworkX
        """
        self.graph = graph

    def extract_communication_network(self):
        """
        Extrait le réseau de communication pour visualisation

        Returns:
            dict: Structure du réseau
        """
        # Extraire les noeuds utilisateurs
        users = []
        for node, data in self.graph.nodes(data=True):
            if data.get("type") != "user":
                continue

            users.append({
                "id": node,
                "email": data.get("email", ""),
                "name": data.get("name", ""),
                "is_central": data.get("is_central_user", False),
                "connection_strength": data.get("connection_strength", 0)
            })

        # Extraire les liens entre utilisateurs
        links = []
        for s, t, edge_data in self.graph.edges(data=True):
            if edge_data.get("type") not in ["EMAILED", "EMAILED_CC", "EMAILED_BCC"]:
                continue

            source_data = self.graph.nodes.get(s, {})
            target_data = self.graph.nodes.get(t, {})

            if source_data.get("type") != "user" or target_data.get("type") != "user":
                continue

            links.append({
                "source": s,
                "target": t,
                "type": edge_data.get("type", ""),
                "weight": edge_data.get("weight", 1.0)
            })

        return {
            "nodes": users,
            "links": links
        }