"""
Module Recherche Semantique
Connecte tous les modules : création du graphe, parsing NLP, recherche sémantique.
"""

import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import traceback

# Import des modules du projet
from backend.app.services.email_graph.processor import EmailGraphProcessor
from backend.app.services.email_graph.search.graph_search_engine import GraphSearchEngine
from backend.app.services.semantic_search.models import NaturalLanguageRequest
from backend.app.services.semantic_search.query_transformer import get_query_transformer


class AccordPipeline:
    """
    Pipeline principal d'Accord qui orchestre :
    1. Construction du graphe d'emails
    2. Transformation de requêtes NLP en sémantique
    3. Recherche dans le graphe
    4. Formatage des résultats
    """

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

    def initialize_graph(self, emails: List[Dict[str, Any]], central_user: str, max_emails: Optional[int] = None) -> \
    Dict[str, Any]:
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
            print(f"\n Initialisation du graphe pour {central_user}...")
            print(f" {len(emails)} emails à traiter")

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
            print(result)
            if result.get('status') == 'error':
                raise Exception(f"Erreur construction graphe: {result.get('message')}")

            # Initialiser le moteur de recherche
            print("Initialisation du moteur de recherche...")
            self.search_engine = GraphSearchEngine(self.graph_processor.graph)

            # Statistiques
            build_time = time.time() - start_time
            self.stats['graph_build_time'] = build_time
            self.stats['last_update'] = datetime.now()

            graph_stats = {
                'nodes': self.graph_processor.graph.number_of_nodes(),
                'edges': self.graph_processor.graph.number_of_edges(),
                'messages': len(self.search_engine.message_nodes),
                'users': len(self.search_engine.user_nodes),
                'threads': len(self.search_engine.thread_nodes),
                'build_time_seconds': round(build_time, 2)
            }

            print(f" Graphe construit en {build_time:.2f}s")
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
            print("Initialisation du module NLP...")
            self.query_transformer = get_query_transformer()
            print(" Module NLP prêt")
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
            print(f"\n Recherche: '{query}'")
            print("*******************************************")

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
            print("\n Recherche dans le graphe...")
            print("************************************************")
            search_results = self.search_engine.search(semantic_query)

            print(f" {len(search_results)} résultats trouvés")

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
                'messages': len(self.search_engine.message_nodes) if self.search_engine else 0,
                'users': len(self.search_engine.user_nodes) if self.search_engine else 0,
                'threads': len(self.search_engine.thread_nodes) if self.search_engine else 0,
                'terms_indexed': len(self.search_engine.inverted_index) if self.search_engine else 0
            }
        }



def debug_search_engine(search_engine):
    """Fonction de debug pour diagnostiquer l'indexation"""

    print("\n" + "=" * 50)
    print("DEBUG - ÉTAT DE L'INDEX DE RECHERCHE")
    print("=" * 50)

    # Vérifier les index
    print(f"📊 Messages indexés: {len(search_engine.message_nodes)}")
    print(f"📊 Utilisateurs indexés: {len(search_engine.user_nodes)}")
    print(f"📊 Threads indexés: {len(search_engine.thread_nodes)}")
    print(f"📊 Termes dans l'index inversé: {len(search_engine.inverted_index)}")

    # Échantillon de termes indexés
    if search_engine.inverted_index:
        sample_terms = list(search_engine.inverted_index.keys())[:10]
        print(f"\n Premiers termes indexés: {sample_terms}")

    # Vérifier les utilisateurs créés
    print(f"\n👥 Utilisateurs créés:")
    for user_id, user_data in search_engine.user_nodes.items():
        email = user_data.get('email', 'No email')
        name = user_data.get('name', 'No name')
        print(f"   {user_id}: {name} <{email}>")

    # Vérifier quelques messages avec leur TF
    print(f"\n Échantillon de messages indexés:")
    for i, (msg_id, msg_data) in enumerate(search_engine.message_nodes.items()):
        if i < 3:
            print(f"   {msg_id}:")
            print(f"      Sujet: {msg_data.get('subject', 'No subject')}")
            print(f"      De: {msg_data.get('from', 'No sender')}")
            tf_terms = list(msg_data.get('_tf', {}).keys())[:8]
            print(f"      Termes TF: {tf_terms}")
            topics = msg_data.get('topics', [])
            print(f"      Topics: {topics}")

    # Vérifier l'index temporel
    print(f"\n Index temporel:")
    sample_dates = list(search_engine.temporal_index.keys())[:5]
    for date_key in sample_dates:
        count = len(search_engine.temporal_index[date_key])
        print(f"   {date_key}: {count} message(s)")

    print("=" * 50)

def create_test_pipeline():
    """Crée un pipeline de test avec des données COHÉRENTES"""
    from datetime import timedelta

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
            "content": "Voici votre facture mensuelle pour janvier. Montant total 1500€. Merci de procéder au paiement avant le 15."
        },
        {
            "subject": "Projet IA - Rapport hebdomadaire",
            "topics": ["projet", "ia", "rapport"],
            "content": "Rapport hebdomadaire du projet intelligence artificielle. Avancement des développements et prochaines étapes."
        },
        {
            "subject": "Newsletter tech - Actualités développement",
            "topics": ["newsletter", "actualites", "tech"],
            "content": "Newsletter hebdomadaire avec les dernières actualités technologiques et tendances développement."
        },
        {
            "subject": "Réunion équipe - Notes importantes",
            "topics": ["meeting", "important", "notes"],
            "content": "Notes de la réunion équipe avec décisions importantes et actions à suivre. Pièces jointes incluses."
        },
        {
            "subject": "Commande matériel bureau",
            "topics": ["commande", "materiel"],
            "content": "Commande de nouveau matériel pour le bureau. Ordinateurs portables et écrans. Livraison prévue."
        }
    ]

    # Générer 20 emails plus réalistes
    test_emails = []
    for i in range(20):
        contact = contacts[i % len(contacts)]
        subject_info = subjects_and_topics[i % len(subjects_and_topics)]

        # Dates plus cohérentes - emails récents
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
            "is_important": i % 7 == 0,  # ~14% sont importants 
            "is_unread": i < 5,  # Les 5 premiers sont non lus
            "topics": subject_info["topics"]  
        })

    print(f"Génération de {len(test_emails)} emails de test")
    print(f"Du {test_emails[-1]['Date'][:10]} au {test_emails[0]['Date'][:10]}")

    pipeline = AccordPipeline()

    init_result = pipeline.initialize_graph(
        emails=test_emails,
        central_user="user@company.com"
    )

    if init_result['success']:
        print("\n Pipeline de test créé avec succès!")
        print(f"   Statistiques: {init_result['stats']}")

        # A decommenter pour debugger
        #debug_search_engine(pipeline.search_engine)

    else:
        print(f"\n❌ Erreur création pipeline: {init_result['error']}")

    return pipeline  


def main():
    print("=" * 60)
    print("ACCORD - Pipeline de Recherche Sémantique")
    print("=" * 60)

    # Créer le pipeline de test
    pipeline = create_test_pipeline()
    print(pipeline)
    if not pipeline.is_initialized:
        print("Échec de l'initialisation du pipeline")
        return

    # quelques exemples de requêtes
    test_queries = [
        "emails de Marie sur les factures",
        "messages d'hier",
        "projet IA",
        "emails importants avec pièces jointes",
        "newsletter",
        "newletter"
    ]

    print("\n" + "=" * 60)
    print("TEST DES REQUÊTES")
    print("=" * 60)

    for query in test_queries:
        result = pipeline.search(query)

        if result['success']:
            print("=============================================")
            print(f"\n Requête: '{query}'")
            print(f"   Résultats: {result['stats']['total_results']}")
            print(f"   Temps total: {result['stats']['search_time_ms']}ms")

            for i, res in enumerate(result['results']):
                print(f"\n   #{i + 1} [{res['scores']['total']:.3f}]")
                print(f"      Sujet: {res['metadata']['subject']}")
                print(f"      De: {res['metadata']['sender']['name']} <{res['metadata']['sender']['email']}>")
                print(f"      Date: {res['metadata']['date']}")
                if res['snippet']:
                    print(f"      Extrait: {res['snippet']}")
            print("=====================================================")
        else:
            print(f"\n❌ Erreur pour '{query}': {result['error']}")

    # Afficher les statistiques finales
    print("\n" + "=" * 60)
    print("STATISTIQUES DU PIPELINE")
    print("=" * 60)
    stats = pipeline.get_pipeline_stats()
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()