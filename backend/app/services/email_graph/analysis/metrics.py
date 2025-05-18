"""
Analyseur de métriques pour le graphe d'emails.
"""

from collections import defaultdict
from datetime import datetime


class GraphMetricsAnalyzer:
    """Classe pour l'analyse des métriques du graphe d'emails."""

    def __init__(self, graph):
        """
        Initialise l'analyseur de métriques

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

    def get_top_contacts(self, limit=10):
        """
        Identifie les contacts les plus importants

        Args:
            limit (int): Nombre maximum de contacts à retourner

        Returns:
            list: Liste de contacts avec leurs métriques
        """
        contacts = []

        for node, data in self.graph.nodes(data=True):
            if data.get("type") != "user" or data.get("is_central_user", False):
                continue

            contact = {
                "id": node,
                "email": data.get("email", ""),
                "name": data.get("name", ""),
                "domain": data.get("domain", ""),
                "connection_strength": data.get("connection_strength", 0)
            }

            # Compter les emails envoyés et reçus
            sent_count = 0
            received_count = 0

            for s, t, edge_data in self.graph.edges(data=True):
                if edge_data.get("type") == "EMAILED" and s == node:
                    sent_count += 1
                elif edge_data.get("type") == "EMAILED" and t == node:
                    received_count += 1

            contact["sent_count"] = sent_count
            contact["received_count"] = received_count

            contacts.append(contact)

        # Trier par force de connexion
        contacts.sort(key=lambda x: x["connection_strength"], reverse=True)

        return contacts[:limit]

    def get_top_threads(self, limit=5):
        """
        Identifie les fils de discussion les plus actifs

        Args:
            limit (int): Nombre maximum de fils à retourner

        Returns:
            list: Liste de fils avec leurs métriques
        """
        threads = []

        for node, data in self.graph.nodes(data=True):
            if data.get("type") != "thread":
                continue

            thread = {
                "id": node,
                "message_count": data.get("message_count", 0),
                "last_message_date": data.get("last_message_date", ""),
                "participants": data.get("participants", []),
                "topics": data.get("topics", []),
                "subject": data.get("subject", "")
            }

            threads.append(thread)

        # Trier par nombre de messages
        threads.sort(key=lambda x: x["message_count"], reverse=True)

        return threads[:limit]



    def calculate_stats(self):
        """
        Calcule les statistiques générales du graphe

        Returns:
            dict: Statistiques
        """
        # Statistiques de base du graphe
        stats = {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "node_types": {},
            "edge_types": {}
        }

        # Compter les types de noeuds
        node_types = defaultdict(int)
        for _, data in self.graph.nodes(data=True):
            node_type = data.get("type", "unknown")
            node_types[node_type] += 1

        stats["node_types"] = dict(node_types)

        # Compter les types de relations
        edge_types = defaultdict(int)
        for _, _, data in self.graph.edges(data=True):
            edge_type = data.get("type", "unknown")
            edge_types[edge_type] += 1

        stats["edge_types"] = dict(edge_types)

        # Statistiques de centralité (seulement si le graphe a des noeuds)
        if self.graph.number_of_nodes() > 0:
            try:
                import networkx as nx

                # Degré de centralité
                degree_centrality = nx.degree_centrality(self.graph)
                stats["top_degree_centrality"] = self._get_top_nodes_by_metric(degree_centrality, 5)

                # Centralité d'intermédiarité
                betweenness_centrality = nx.betweenness_centrality(self.graph)
                stats["top_betweenness_centrality"] = self._get_top_nodes_by_metric(betweenness_centrality, 5)

            except Exception as e:
                print(f"Erreur lors du calcul des métriques de centralité: {str(e)}")
                stats["centrality_error"] = str(e)

        return stats

    def _get_top_nodes_by_metric(self, metric_dict, limit=5):
        """
        Récupère les noeuds les mieux classés selon une métrique

        Args:
            metric_dict (dict): Dictionnaire node_id -> valeur_métrique
            limit (int): Nombre maximum de noeuds à retourner

        Returns:
            list: Noeuds les mieux classés
        """
        # Trier les noeuds par la métrique
        sorted_nodes = sorted(metric_dict.items(), key=lambda x: x[1], reverse=True)

        # Construire les résultats
        results = []
        count = 0

        for node_id, value in sorted_nodes:
            if count >= limit:
                break

            # Vérifier si c'est un noeud utilisateur (pour les métriques de centralité)
            node_data = self.graph.nodes.get(node_id, {})
            if node_data.get("type") != "user":
                continue

            results.append({
                "id": node_id,
                "email": node_data.get("email", ""),
                "name": node_data.get("name", ""),
                "value": value
            })

            count += 1

        return results