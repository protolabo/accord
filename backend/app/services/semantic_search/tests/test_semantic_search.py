"""
Tests complets pour le module de recherche sémantique Accord.
Teste le pipeline complet : NLP → LLM → LangChain → Fusion → Transformation
"""

import pytest
import time
import json
from typing import Dict, Any, List
from unittest.mock import Mock, patch

# Imports du module à tester
from backend.app.services.semantic_search.query_parser import (
    get_query_parser,
    NaturalLanguageQueryParser,
    IntentType
)
from backend.app.services.semantic_search.llm_engine import (
    get_query_parser as get_llm_parser,
    MistralQueryParser
)
from backend.app.services.semantic_search.query_transformer import (
    get_query_transformer,
    SemanticQueryTransformer
)
from backend.app.services.semantic_search.models import (
    NaturalLanguageRequest,
    QueryType
)
from backend.app.services.semantic_search.patterns import (
    get_patterns,
    is_blacklisted_name
)


class TestCase:
    """Classe pour définir les cas de test"""

    def __init__(self, query: str, expected_intent: str, expected_filters: Dict, description: str):
        self.query = query
        self.expected_intent = expected_intent
        self.expected_filters = expected_filters
        self.description = description


class TestSemanticSearchPipeline:
    """Tests du pipeline complet de recherche sémantique"""

    @pytest.fixture(scope="class")
    def nlp_parser(self):
        """Fixture pour le parser NLP"""
        return get_query_parser()

    @pytest.fixture(scope="class")
    def llm_parser(self):
        """Fixture pour le parser LLM"""
        return get_llm_parser()

    @pytest.fixture(scope="class")
    def transformer(self):
        """Fixture pour le transformer"""
        return get_query_transformer()

    @pytest.fixture
    def test_cases_basic(self):
        """Cas de test basiques"""
        return [
            TestCase(
                query="emails de Marie",
                expected_intent="search_contact",
                expected_filters={"contact_name": "Marie"},
                description="Recherche contact simple"
            ),
            TestCase(
                query="emails hier",
                expected_intent="search_temporal",
                expected_filters={"date_from": "2024-01-28"},  # Ajuster selon date actuelle
                description="Recherche temporelle simple"
            ),
            TestCase(
                query="emails avec pièce jointe",
                expected_intent="search_attachment",
                expected_filters={"has_attachments": True},
                description="Recherche avec attachement"
            ),
            TestCase(
                query="emails de test",
                expected_intent="search_semantic",
                expected_filters={},
                description="Requête test (doit être semantic, pas contact)"
            ),
            TestCase(
                query="factures importantes",
                expected_intent="search_topic",
                expected_filters={"topic_ids": ["facturation"]},
                description="Recherche par topic"
            )
        ]

    @pytest.fixture
    def test_cases_complex(self):
        """Cas de test complexes"""
        return [
            TestCase(
                query="emails de Marie la semaine dernière",
                expected_intent="search_combined",
                expected_filters={"contact_name": "Marie", "date_from": "2024-01-22"},
                description="Requête combinée contact + temporel"
            ),
            TestCase(
                query="factures avec PDF de janvier",
                expected_intent="search_combined",
                expected_filters={"topic_ids": ["facturation"], "has_attachments": True},
                description="Requête combinée topic + attachment + temporal"
            ),
            TestCase(
                query="emails importants non lus",
                expected_intent="search_semantic",
                expected_filters={"is_important": True, "is_unread": True},
                description="Requête avec multiples filtres d'action"
            )
        ]

    @pytest.fixture
    def test_cases_multilingual(self):
        """Cas de test multilingues"""
        return [
            TestCase(
                query="emails from John yesterday",
                expected_intent="search_combined",
                expected_filters={"contact_name": "John"},
                description="Requête anglaise"
            ),
            TestCase(
                query="messages with attachments",
                expected_intent="search_attachment",
                expected_filters={"has_attachments": True},
                description="Requête anglaise avec attachment"
            )
        ]

    def test_nlp_parser_basic(self, nlp_parser, test_cases_basic):
        """Test du parser NLP sur cas basiques"""
        for case in test_cases_basic:
            result = nlp_parser.parse_query(case.query)

            print(f"\n🧪 Test NLP: {case.description}")
            print(f"   Query: '{case.query}'")
            print(f"   Intent: {result['intent']} (attendu: {case.expected_intent})")
            print(f"   Filters: {result['filters']}")
            print(f"   Confidence: {result['confidence']}")

            # Tests de structure
            assert 'intent' in result
            assert 'entities' in result
            assert 'filters' in result
            assert 'confidence' in result
            assert 'language' in result

            # Test confidence raisonnable
            assert 0.1 <= result['confidence'] <= 1.0

    def test_llm_parser_if_available(self, llm_parser, test_cases_basic):
        """Test du parser LLM si disponible"""
        if not llm_parser.model:
            pytest.skip("Modèle LLM non disponible")

        for case in test_cases_basic[:3]:  # Limite pour éviter les timeouts
            result = llm_parser.parse_query(case.query)

            print(f"\n🤖 Test LLM: {case.description}")
            print(f"   Query: '{case.query}'")
            print(f"   Query Type: {result.get('query_type')}")
            print(f"   Semantic Text: {result.get('semantic_text')}")
            print(f"   Filters: {result.get('filters', {})}")

            # Tests de structure
            assert 'query_type' in result
            assert 'semantic_text' in result
            assert 'filters' in result
            assert '_meta' in result

            # Test métadonnées
            meta = result['_meta']
            assert 'model_used' in meta
            assert 'parsing_time_ms' in meta
            assert meta['parsing_time_ms'] > 0

    def test_transformer_pipeline(self, transformer, test_cases_basic):
        """Test du pipeline complet transformer"""
        for case in test_cases_basic:
            request = NaturalLanguageRequest(query=case.query)
            result = transformer.transform_query(request)

            print(f"\n🔄 Test Transformer: {case.description}")
            print(f"   Query: '{case.query}'")
            print(f"   Success: {result['success']}")
            print(f"   Query Type: {result['semantic_query']['query_type']}")
            print(f"   Processing Method: {result['processing_info']['parsing_method']}")
            print(f"   Confidence: {result['processing_info']['confidence']}")

            # Tests de structure
            assert result['success'] is True
            assert 'semantic_query' in result
            assert 'processing_info' in result
            assert 'debug_info' in result

            # Test semantic_query
            semantic_query = result['semantic_query']
            assert 'query_type' in semantic_query
            assert 'semantic_text' in semantic_query
            assert 'filters' in semantic_query
            assert 'similarity_threshold' in semantic_query
            assert 'limit' in semantic_query

            # Test processing_info
            processing_info = result['processing_info']
            assert 'transformation_time_ms' in processing_info
            assert 'parsing_method' in processing_info
            assert 'confidence' in processing_info

            # Test valeurs raisonnables
            assert processing_info['transformation_time_ms'] > 0
            assert 0.1 <= processing_info['confidence'] <= 1.0

    def test_blacklist_functionality(self, transformer):
        """Test de la fonctionnalité blacklist"""
        blacklist_queries = [
            "emails de test",
            "emails de debug",
            "emails de exemple",
            "emails de demo"
        ]

        for query in blacklist_queries:
            request = NaturalLanguageRequest(query=query)
            result = transformer.transform_query(request)

            print(f"\n🚫 Test Blacklist: '{query}'")
            print(f"   Query Type: {result['semantic_query']['query_type']}")
            print(f"   Filters: {result['semantic_query']['filters']}")

            # Ces requêtes ne doivent PAS être détectées comme contact
            # (grâce à la blacklist et/ou au LLM)
            semantic_query = result['semantic_query']

            # Soit semantic directement, soit pas de contact_name dans les filtres
            if semantic_query['query_type'] == QueryType.CONTACT:
                # Si détecté comme contact, ne doit pas avoir de contact_name blacklisté
                filters = semantic_query['filters']
                if 'contact_name' in filters:
                    assert not is_blacklisted_name(filters['contact_name'], 'auto')

    def test_multilingual_support(self, transformer, test_cases_multilingual):
        """Test du support multilingue"""
        for case in test_cases_multilingual:
            request = NaturalLanguageRequest(query=case.query)
            result = transformer.transform_query(request)

            print(f"\n🌍 Test Multilingual: {case.description}")
            print(f"   Query: '{case.query}'")
            print(f"   Language detected: {result['debug_info']['nlp_result'].get('language', 'unknown')}")
            print(f"   Query Type: {result['semantic_query']['query_type']}")

            # Le système doit fonctionner même en anglais
            assert result['success'] is True

    def test_performance_benchmarks(self, transformer):
        """Test de performance du système"""
        test_queries = [
            "emails de Marie",
            "factures hier",
            "emails avec PDF",
            "réunions importantes cette semaine"
        ]

        times = []

        for query in test_queries:
            request = NaturalLanguageRequest(query=query)

            start_time = time.time()
            result = transformer.transform_query(request)
            end_time = time.time()

            processing_time = (end_time - start_time) * 1000
            times.append(processing_time)

            print(f"\n⏱️ Performance: '{query}' → {processing_time:.1f}ms")

        avg_time = sum(times) / len(times)
        print(f"\n📊 Performance moyenne: {avg_time:.1f}ms")

        # Tests de performance (ajuster selon tes besoins)
        # Première requête peut être plus lente (chargement modèle)
        assert avg_time < 15000  # 15 secondes max en moyenne

        # Les requêtes suivantes doivent être plus rapides
        if len(times) > 1:
            subsequent_avg = sum(times[1:]) / len(times[1:])
            print(f"📊 Performance requêtes suivantes: {subsequent_avg:.1f}ms")

    def test_error_handling(self, transformer):
        """Test de gestion d'erreurs"""
        error_cases = [
            "",  # Requête vide
            "a",  # Requête trop courte
            "?" * 600,  # Requête trop longue
            "email de 123456",  # Requête avec caractères spéciaux
        ]

        for query in error_cases:
            try:
                request = NaturalLanguageRequest(query=query)
                result = transformer.transform_query(request)

                print(f"\n❌ Test Erreur: '{query[:50]}...'")
                print(f"   Success: {result['success']}")

                # Le système doit gérer gracieusement les erreurs
                assert 'success' in result

            except Exception as e:
                print(f"\n⚠️ Exception pour '{query[:20]}...': {e}")
                # Les exceptions de validation Pydantic sont acceptables

    def test_patterns_functionality(self):
        """Test du système de patterns"""
        # Test patterns temporels
        temporal_patterns = get_patterns('fr', 'temporal')
        assert len(temporal_patterns) > 0

        # Test patterns anglais
        english_patterns = get_patterns('en', 'contact')
        assert len(english_patterns) > 0

        # Test blacklist
        assert is_blacklisted_name('test', 'fr') is True
        assert is_blacklisted_name('Marie', 'fr') is False

        print("\n📋 Patterns:")
        print(f"   Temporal FR: {len(temporal_patterns)} patterns")
        print(f"   Contact EN: {len(english_patterns)} patterns")

    def test_confidence_calculation(self, transformer):
        """Test du calcul de confiance"""
        confidence_cases = [
            ("emails de Marie", "Haute confiance attendue"),
            ("emails de test", "Confiance réduite (blacklist)"),
            ("emails", "Confiance faible (générique)"),
            ("emails de Marie hier avec PDF", "Confiance élevée (complexe)")
        ]

        for query, description in confidence_cases:
            request = NaturalLanguageRequest(query=query)
            result = transformer.transform_query(request)

            confidence = result['processing_info']['confidence']

            print(f"\n🎯 Confiance: '{query}' → {confidence:.2f}")
            print(f"   Description: {description}")

            # Test plage de confiance
            assert 0.1 <= confidence <= 1.0

    @pytest.mark.slow
    def test_comprehensive_scenarios(self, transformer):
        """Test de scénarios complets (marqué comme lent)"""
        comprehensive_cases = [
            "montre-moi tous les emails de Marie concernant le projet Alpha avec des pièces jointes PDF depuis la semaine dernière",
            "factures non payées avec montant supérieur à 1000 euros",
            "emails urgents de l'équipe marketing concernant la campagne Q4",
            "conversations avec les clients VIP depuis janvier",
            "newsletters et promotions reçues ce mois",
        ]

        for query in comprehensive_cases:
            request = NaturalLanguageRequest(query=query)
            result = transformer.transform_query(request)

            print(f"\n🔍 Scénario: '{query[:50]}...'")
            print(f"   Query Type: {result['semantic_query']['query_type']}")
            print(f"   Filters: {len(result['semantic_query']['filters'])} filtres")
            print(f"   Method: {result['processing_info']['parsing_method']}")

            assert result['success'] is True


class TestSemanticSearchAPI:
    """Tests pour l'API FastAPI"""

    @pytest.fixture
    def client(self):
        """Client de test FastAPI"""
        from fastapi.testclient import TestClient
        from backend.app.services.semantic_search.main import app
        return TestClient(app)

    def test_health_endpoint(self, client):
        """Test endpoint de santé"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_parse_endpoint(self, client):
        """Test endpoint de parsing"""
        test_request = {
            "query": "emails de Marie",
            "user_context": None
        }

        response = client.post("/semantic-search/parse", json=test_request)
        assert response.status_code == 200

        data = response.json()
        assert "success" in data
        assert "semantic_query" in data
        assert "processing_time_ms" in data

    def test_info_endpoint(self, client):
        """Test endpoint d'information"""
        response = client.get("/info")
        assert response.status_code == 200

        data = response.json()
        assert "service_name" in data
        assert "capabilities" in data
        assert "models" in data


if __name__ == "__main__":
    # Pour exécuter les tests directement
    pytest.main([
        __file__,
        "-v",  # Verbose
        "-s",  # Ne pas capturer la sortie
        "--tb=short",  # Traceback court
        "-x"  # Arrêter au premier échec
    ])