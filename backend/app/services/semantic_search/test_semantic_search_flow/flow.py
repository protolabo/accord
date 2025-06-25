"""
Module Recherche Semantique
 création du graphe, parsing NLP, recherche sémantique.
"""

import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import traceback
import random
import argparse

# Import des modules du projet
from backend.app.services.email_graph.processor import EmailGraphProcessor
from backend.app.services.email_graph.search.search_manager import GraphSearchEngine
from backend.app.services.semantic_search.models import NaturalLanguageRequest
from backend.app.services.semantic_search.query_transformer import get_query_transformer


class AccordPipeline:

    def __init__(self):
        """Initialise le pipeline"""
        self.graph_processor = None
        self.search_engine = None
        self.query_transformer = None
        self.is_initialized = False
        self.stats = {
            'graph_build_time': 0,
            'total_searches': 0,
            'avg_search_time': 0,
            'last_update': None
        }

    def initialize_graph(self, emails: List[Dict[str, Any]], central_user: str, max_emails: Optional[int] = None) -> Dict[str, Any]:
        """
        Initialise ou met à jour le graphe d'emails

        Args:
            emails: Liste des emails à traiter
            central_user: Email de l'utilisateur central
            max_emails: Nombre maximum d'emails à traiter

        Returns:
            Résultat de la construction du graphe
        """
        start_time = time.time()

        try:
            print(f"\n🚀 Initialisation du graphe pour {central_user}...")
            print(f"📧 {len(emails)} emails à traiter")

            self.graph_processor = EmailGraphProcessor()

            # Préparer les données
            graph_input = {
                "mails": emails,
                "central_user": central_user,
                "max_emails": max_emails
            }

            # Construire le graphe
            result_json = self.graph_processor.process_graph(json.dumps(graph_input))
            result = json.loads(result_json)

            if result.get('status') == 'error':
                raise Exception(f"Erreur construction graphe: {result.get('message')}")

            # Initialiser le moteur de recherche
            print("🔍 Initialisation du moteur de recherche...")
            self.search_engine = GraphSearchEngine(self.graph_processor.graph)

            # Statistiques
            build_time = time.time() - start_time
            self.stats['graph_build_time'] = build_time
            self.stats['last_update'] = datetime.now()

            # Accéder aux statistiques via la méthode correcte
            search_stats = self.search_engine.get_search_statistics()
            index_stats = search_stats.get('index_stats', {})

            graph_stats = {
                'nodes': self.graph_processor.graph.number_of_nodes(),
                'edges': self.graph_processor.graph.number_of_edges(),
                'messages': index_stats.get('messages', 0),
                'users': index_stats.get('users', 0),
                'threads': index_stats.get('threads', 0),
                'build_time_seconds': round(build_time, 2)
            }

            print(f"✅ Graphe construit en {build_time:.2f}s")
            print(f"   - {graph_stats['nodes']} nœuds")
            print(f"   - {graph_stats['edges']} relations")
            print(f"   - {graph_stats['messages']} messages indexés")

            self.is_initialized = True

            return {
                'success': True,
                'stats': graph_stats,
                'result': result
            }

        except Exception as e:
            print(f"❌ Erreur initialisation graphe: {str(e)}")
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'trace': traceback.format_exc()
            }

    def initialize_nlp(self) -> bool:
        """Initialise le module de transformation NLP/sémantique"""
        try:
            print("🧠 Initialisation du module NLP...")
            self.query_transformer = get_query_transformer()
            print("✅ Module NLP prêt")
            return True
        except Exception as e:
            print(f"❌ Erreur initialisation NLP: {str(e)}")
            return False

    def search(self, query: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Exécute une recherche complète : NLP -> Sémantique -> Graphe

        Args:
            query: Requête en langage naturel
            user_context: Contexte utilisateur (timezone, préférences, etc.)

        Returns:
            Résultats de recherche avec métadonnées complètes
        """
        if not self.is_initialized:
            return {
                'success': False,
                'error': 'Pipeline non initialisé. Appelez initialize_graph() d\'abord.'
            }

        start_time = time.time()

        try:
            # Phase 1 : Transformation NLP -> Sémantique
            print(f"\n🔍 Recherche: '{query}'")
            print("*" * 50)

            if not self.query_transformer:
                self.initialize_nlp()

            nl_request = NaturalLanguageRequest(
                query=query,
                user_context=user_context
            )

            transform_result = self.query_transformer.transform_query(nl_request)

            if not transform_result['success']:
                return {
                    'success': False,
                    'error': "Échec de l'analyse sémantique",
                    'details': transform_result
                }

            semantic_query = transform_result['semantic_query']

            print(f"   Type: {semantic_query['query_type']}")
            print(f"   Texte: '{semantic_query['semantic_text']}'")
            if semantic_query['filters']:
                print(f"   Filtres: {semantic_query['filters']}")

            # Phase 2 : Recherche dans le graphe
            print("\n🎯 Recherche dans le graphe...")
            search_results = self.search_engine.search(semantic_query)

            print(f"✅ {len(search_results)} résultats trouvés")

            # Phase 3 : Formatage des résultats
            formatted_results = [result.to_dict() for result in search_results]

            # Statistiques
            search_time = time.time() - start_time
            self.stats['total_searches'] += 1
            self.stats['avg_search_time'] = (
                    (self.stats['avg_search_time'] * (self.stats['total_searches'] - 1) + search_time)
                    / self.stats['total_searches']
            )

            return {
                'success': True,
                'query': {
                    'original': query,
                    'parsed': semantic_query,
                    'parsing_info': transform_result['processing_info']
                },
                'results': formatted_results,
                'stats': {
                    'total_results': len(search_results),
                    'search_time_ms': round(search_time * 1000, 2),
                    'parsing_time_ms': transform_result['processing_info']['transformation_time_ms'],
                    'graph_search_time_ms': round((search_time * 1000) -
                                                  transform_result['processing_info']['transformation_time_ms'], 2)
                }
            }

        except Exception as e:
            print(f"❌ Erreur recherche: {str(e)}")
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'trace': traceback.format_exc()
            }

    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du pipeline"""
        index_stats = {}
        if self.search_engine:
            search_stats = self.search_engine.get_search_statistics()
            index_stats = search_stats.get('index_stats', {})

        return {
            'graph': {
                'is_initialized': self.is_initialized,
                'last_update': self.stats['last_update'].isoformat() if self.stats['last_update'] else None,
                'build_time_seconds': self.stats['graph_build_time'],
                'nodes': self.graph_processor.graph.number_of_nodes() if self.graph_processor else 0,
                'edges': self.graph_processor.graph.number_of_edges() if self.graph_processor else 0
            },
            'search': {
                'total_searches': self.stats['total_searches'],
                'avg_search_time_ms': round(self.stats['avg_search_time'] * 1000, 2)
            },
            'index': {
                'messages': index_stats.get('messages', 0),
                'users': index_stats.get('users', 0),
                'threads': index_stats.get('threads', 0),
                'terms_indexed': index_stats.get('unique_terms', 0)
            }
        }


class TestDataGenerator:
    """Générateur de données de test pour le pipeline"""

    @staticmethod
    def create_basic_test_data(num_emails: int = 20) -> List[Dict[str, Any]]:
        """Crée des données de test basiques"""
        base_date = datetime.now()

        contacts = [
            {"email": "marie@company.com", "name": "Marie Dupont"},
            {"email": "jean@client.com", "name": "Jean Martin"},
            {"email": "support@service.com", "name": "Support Service"}
        ]

        subjects_and_topics = [
            {
                "subject": "Facture mensuelle janvier 2025",
                "topics": ["facturation", "billing"],
                "content": "Voici votre facture mensuelle pour janvier. Montant total 1500€."
            },
            {
                "subject": "Projet IA - Rapport hebdomadaire",
                "topics": ["projet", "ia", "rapport"],
                "content": "Rapport hebdomadaire du projet intelligence artificielle."
            },
            {
                "subject": "Newsletter tech - Actualités",
                "topics": ["newsletter", "actualites", "tech"],
                "content": "Newsletter hebdomadaire avec les dernières actualités."
            },
            {
                "subject": "Réunion équipe - Notes importantes",
                "topics": ["meeting", "important", "notes"],
                "content": "Notes de la réunion équipe avec décisions importantes."
            },
            {
                "subject": "Commande matériel bureau",
                "topics": ["commande", "materiel"],
                "content": "Commande de nouveau matériel pour le bureau."
            }
        ]

        test_emails = []
        for i in range(num_emails):
            contact = contacts[i % len(contacts)]
            subject_info = subjects_and_topics[i % len(subjects_and_topics)]
            email_date = base_date - timedelta(days=i)

            test_emails.append({
                "Message-ID": f"msg{i:03d}@company.com",
                "Thread-ID": f"thread{i // 3:03d}",
                "From": contact["email"],
                "To": "user@company.com",
                "Subject": subject_info["subject"],
                "Content": subject_info["content"],
                "Date": email_date.isoformat(),
                "has_attachments": i % 5 == 0,
                "attachment_count": 2 if i % 5 == 0 else 0,
                "is_important": i % 7 == 0,
                "is_unread": i < 5,
                "topics": subject_info["topics"]
            })

        return test_emails

    @staticmethod
    def create_enhanced_test_data(num_emails: int = 50) -> List[Dict[str, Any]]:
        """Crée des données de test enrichies pour couvrir tous les cas"""
        base_date = datetime.now()

        # Contacts variés
        contacts = [
            {"email": "marie.dupont@company.com", "name": "Marie Dupont"},
            {"email": "pierre.martin@client.com", "name": "Pierre Martin"},
            {"email": "jean.bernard@partner.com", "name": "Jean Bernard"},
            {"email": "support@service.com", "name": "Support Service"},
            {"email": "newsletter@news.com", "name": "Newsletter Service"},
            {"email": "facture@billing.com", "name": "Service Facturation"},
            {"email": "livraison@shipping.com", "name": "Service Livraison"},
            {"email": "equipe@company.com", "name": "Équipe Marketing"}
        ]

        # Templates d'emails variés
        email_templates = [
            {
                "subject": "Budget prévisionnel Q1 2025",
                "content": "Voici le budget détaillé pour le premier trimestre 2025.",
                "topics": ["budget", "finance"],
                "attachments": [{"filename": "budget_q1_2025.xlsx", "size": "245KB"}]
            },
            {
                "subject": "Projet X - Mise à jour importante",
                "content": "Le projet X avance bien. Voici les dernières mises à jour.",
                "topics": ["projet", "update"],
                "attachments": []
            },
            {
                "subject": "Rapport de performance mensuel",
                "content": "Analyse détaillée de la performance de notre équipe.",
                "topics": ["performance", "rapport"],
                "attachments": [{"filename": "performance_report.pdf", "size": "1.2MB"}]
            },
            {
                "subject": "Facture #2025-001",
                "content": "Veuillez trouver ci-joint la facture pour les services.",
                "topics": ["facturation", "billing"],
                "attachments": [{"filename": "facture_2025_001.pdf", "size": "150KB"}]
            },
            {
                "subject": "Newsletter Tech - Janvier 2025",
                "content": "Les dernières actualités technologiques du mois.",
                "topics": ["newsletter", "tech"],
                "attachments": []
            },
            {
                "subject": "Confirmation de livraison",
                "content": "Votre commande a été expédiée et sera livrée demain.",
                "topics": ["livraison", "shipping"],
                "attachments": [{"filename": "bon_livraison.pdf", "size": "80KB"}]
            },
            {
                "subject": "Réunion équipe - Notes importantes",
                "content": "Compte-rendu de la réunion avec les décisions prises.",
                "topics": ["meeting", "important"],
                "attachments": [{"filename": "meeting_notes.docx", "size": "45KB"}]
            },
            {
                "subject": "Message urgent - Action requise",
                "content": "Ce message nécessite votre attention immédiate.",
                "topics": ["urgent", "important"],
                "attachments": []
            }
        ]

        test_emails = []
        central_user = "user@company.com"

        for i in range(num_emails):
            template = random.choice(email_templates)
            contact = random.choice(contacts)

            # Varier les dates
            days_ago = random.randint(0, 60)
            email_date = base_date - timedelta(days=days_ago)

            # Varier expéditeur/destinataire
            if i % 3 == 0:
                # Email envoyé par l'utilisateur central
                from_email = central_user
                to_email = contact["email"]
            else:
                # Email reçu
                from_email = contact["email"]
                to_email = central_user

            # Ajouter CC parfois
            cc_list = []
            if i % 5 == 0:
                cc_list = [random.choice(contacts)["email"] for _ in range(random.randint(1, 3))]

            email = {
                "Message-ID": f"msg{i:04d}@company.com",
                "Thread-ID": f"thread{i // 4:03d}",
                "From": from_email,
                "To": to_email,
                "Cc": ",".join(cc_list) if cc_list else "",
                "Subject": template["subject"],
                "Content": template["content"],
                "Date": email_date.isoformat(),
                "has_attachments": len(template["attachments"]) > 0,
                "attachment_count": len(template["attachments"]),
                "attachments": template["attachments"],
                "is_important": "important" in template["topics"] or "urgent" in template["topics"],
                "is_unread": i < 10,
                "is_archived": i > 40,
                "topics": template["topics"]
            }

            test_emails.append(email)

        return test_emails


class QueryTester:
    """Testeur de requêtes pour le pipeline"""

    @staticmethod
    def get_all_test_queries() -> List[str]:
        """Retourne la liste complète des requêtes de test"""
        return [
            # 1. Recherche par contenu/mots-clés
            "emails parlant de budget",
            "courriels mentionnant projet X",
            "discussions sur performance",
            "emails avec mot-clé spécifique",

            # 2. Recherche par destinataire/expéditeur
            "emails de Marie",
            "emails envoyés à Pierre",
            "messages pour l'équipe",
            "courriels à destination de Jean",

            # 3. Recherche temporelle simple
            "emails d'hier",
            "messages de la semaine dernière",
            "courriels du mois dernier",
            "mails de l'année dernière",
            "messages récents",
            "emails d'aujourd'hui",

            # 4. Recherche temporelle avancée
            "messages de janvier",
            "courriels entre le 1er et le 15 mars",
            "emails du 15/03/2024",
            "messages du 2024-01-15",
            "courriels de mars 2024",

            # 5. Recherche par type/catégorie
            "emails de livraison",
            "factures",
            "newsletter",

            # 6. Recherche par attributs
            "emails avec pièces jointes",
            "courriels avec PDF",
            "emails non lus",
            "messages importants",
            "courriels archivés",
            "messages envoyés",

            # 7. Recherches combinées
            "emails de Marie avec pièces jointes hier",
            "factures de la semaine dernière",
            "messages importants de ce mois",

            # 8. Recherches négatives
            "emails sans pièces jointes",
            "messages sans importance",
        ]

    @staticmethod
    def test_basic_queries(pipeline: AccordPipeline) -> None:
        """Test des requêtes de base"""
        test_queries = [
            "emails de Marie sur les factures",
            "messages d'hier",
            "projet IA",
            "emails importants avec pièces jointes",
            "newsletter",
            "rapport"
        ]

        print("\n" + "=" * 60)
        print("🧪 TEST DES REQUÊTES DE BASE")
        print("=" * 60)

        for query in test_queries:
            result = pipeline.search(query)

            if result['success']:
                print(f"\n📝 Requête: '{query}'")
                print(f"📊 Résultats: {result['stats']['total_results']}")
                print(f"⏱️ Temps total: {result['stats']['search_time_ms']}ms")

                for i, res in enumerate(result['results'][:2]):
                    print(f"\n   #{i + 1} [Score: {res['scores']['total']:.3f}]")
                    print(f"      📧 Sujet: {res['metadata']['subject']}")
                    print(f"      👤 De: {res['metadata']['sender']['name']} <{res['metadata']['sender']['email']}>")
                    print(f"      📅 Date: {res['metadata']['date']}")
            else:
                print(f"\n❌ Erreur pour '{query}': {result['error']}")

    @staticmethod
    def test_all_queries(pipeline: AccordPipeline) -> Dict[str, Any]:
        """Test exhaustif de toutes les requêtes supportées"""
        test_queries = QueryTester.get_all_test_queries()

        print("\n" + "=" * 80)
        print("🧪 TEST EXHAUSTIF DE TOUTES LES REQUÊTES")
        print("=" * 80)

        results_summary = {
            'success': 0,
            'failed': 0,
            'details': []
        }

        for i, query in enumerate(test_queries, 1):
            print(f"\n[{i}/{len(test_queries)}] Requête: '{query}'")
            print("-" * 60)

            try:
                result = pipeline.search(query)

                if result['success']:
                    parsed = result['query']['parsed']
                    stats = result['stats']

                    print(f"✅ Succès!")
                    print(f"   📊 Type détecté: {parsed['query_type']}")
                    print(f"   🔍 Texte sémantique: '{parsed['semantic_text']}'")
                    print(f"   🏷️ Filtres: {parsed['filters']}")
                    print(f"   📈 Résultats: {stats['total_results']}")
                    print(f"   ⏱️ Temps: {stats['search_time_ms']}ms")

                    results_summary['success'] += 1
                    results_summary['details'].append({
                        'query': query,
                        'success': True,
                        'type': parsed['query_type'],
                        'filters': parsed['filters'],
                        'results_count': stats['total_results']
                    })

                else:
                    print(f"❌ Échec: {result['error']}")
                    results_summary['failed'] += 1
                    results_summary['details'].append({
                        'query': query,
                        'success': False,
                        'error': result['error']
                    })

            except Exception as e:
                print(f"❌ Exception: {str(e)}")
                results_summary['failed'] += 1
                results_summary['details'].append({
                    'query': query,
                    'success': False,
                    'error': str(e)
                })

        # Résumé final
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 80)
        print(f"✅ Réussis: {results_summary['success']}/{len(test_queries)}")
        print(f"❌ Échoués: {results_summary['failed']}/{len(test_queries)}")
        print(f"📈 Taux de succès: {(results_summary['success'] / len(test_queries) * 100):.1f}%")

        # Analyser les types de requêtes
        type_counts = {}
        for detail in results_summary['details']:
            if detail['success']:
                query_type = detail['type']
                type_counts[query_type] = type_counts.get(query_type, 0) + 1

        print("\n📊 Distribution des types de requêtes:")
        for query_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {query_type}: {count}")

        # Requêtes échouées
        if results_summary['failed'] > 0:
            print("\n❌ Requêtes échouées:")
            for detail in results_summary['details']:
                if not detail['success']:
                    print(f"   - '{detail['query']}': {detail['error']}")

        return results_summary


def main():
    """Point d'entrée principal avec options de ligne de commande"""
    parser = argparse.ArgumentParser(description='ACCORD - Pipeline de Recherche Sémantique')
    parser.add_argument('--mode', choices=['basic', 'enhanced', 'full'], default='full',
                       help='Mode de test : basic (20 emails), enhanced (50 emails), full (test complet)')
    parser.add_argument('--debug', action='store_true', help='Activer le mode debug')

    args = parser.parse_args()

    print("=" * 80)
    print("🚀 ACCORD - Pipeline de Recherche Sémantique")
    print(f"📋 Mode: {args.mode.upper()}")
    print("=" * 80)

    # Créer le pipeline
    pipeline = AccordPipeline()

    # Générer les données selon le mode
    if args.mode == 'basic':
        test_emails = TestDataGenerator.create_basic_test_data(20)
        print(f"📧 Mode basique : {len(test_emails)} emails de test")
    elif args.mode == 'enhanced':
        test_emails = TestDataGenerator.create_enhanced_test_data(50)
        print(f"📧 Mode enrichi : {len(test_emails)} emails de test")
    else:  # full
        test_emails = TestDataGenerator.create_enhanced_test_data(100)
        print(f"📧 Mode complet : {len(test_emails)} emails de test")

    # Initialiser le graphe
    init_result = pipeline.initialize_graph(
        emails=test_emails,
        central_user="user@company.com"
    )

    if not init_result['success']:
        print(f"❌ Échec de l'initialisation: {init_result['error']}")
        return

    print(f"\n✅ Pipeline initialisé avec succès!")
    print(f"📊 Stats du graphe: {init_result['stats']}")

    # Lancer les tests selon le mode
    if args.mode == 'basic':
        QueryTester.test_basic_queries(pipeline)
    else:
        QueryTester.test_all_queries(pipeline)

    # Afficher les statistiques finales
    print("\n" + "=" * 80)
    print("📊 STATISTIQUES GLOBALES DU PIPELINE")
    print("=" * 80)
    stats = pipeline.get_pipeline_stats()
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()