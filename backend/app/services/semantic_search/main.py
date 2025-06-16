"""
Point d'entrée FastAPI pour le service de recherche sémantique Accord (version spaCy).
Configure l'application avec tous les endpoints et middlewares nécessaires.
"""

import time
import logging
from contextlib import asynccontextmanager

import psutil
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.endpoints import router
from .core.query_transformer import get_query_transformer
from .services.parsing_service import NLPParsingService
from .config import SPACY_CONFIG


# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire de cycle de vie de l'application"""

    # Startup
    logger.info("🚀 Démarrage du service de recherche sémantique Accord (spaCy)")

    # Pré-chargement des composants pour optimiser les premières requêtes
    logger.info("📥 Pré-chargement des composants...")

    try:
        # Initialiser le parser spaCy
        parser = NLPParsingService()
        if parser.nlp_model:
            model_name = getattr(parser.nlp_model, 'meta', {}).get('name', 'unknown')
            logger.info(f"✅ Modèle spaCy chargé: {model_name}")
        else:
            logger.warning("⚠️ Modèle spaCy non disponible, utilisation des patterns uniquement")

        # Initialiser le transformer
        transformer = get_query_transformer()
        logger.info("✅ Query transformer initialisé")

        # Test de sanité au démarrage
        test_query = "emails de test"
        start_time = time.time()

        # Créer un objet request simple pour le test
        class MockRequest:
            def __init__(self, query):
                self.query = query
                self.user_context = None
                self.central_user_email = None

        test_request = MockRequest(test_query)
        result = transformer.transform_query(test_request)

        test_time = (time.time() - start_time) * 1000

        if result.get('success'):
            logger.info(f"✅ Test de sanité réussi en {test_time:.1f}ms")
        else:
            logger.warning(f"⚠️ Test de sanité échoué: {result.get('error', {}).get('message', 'Unknown')}")

    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation: {e}")

    logger.info("🎯 Service de recherche sémantique prêt (spaCy + patterns)")

    yield

    # Shutdown
    logger.info("🛑 Arrêt du service de recherche sémantique")


# Création de l'application FastAPI
app = FastAPI(
    title="Accord Semantic Search Service (spaCy)",
    description="Service de recherche sémantique pour l'application Accord - Transforme le langage naturel en requêtes structurées (version spaCy uniquement)",
    version="2.0.0",
    lifespan=lifespan
)

# Configuration CORS pour développement
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# Middleware de logging des requêtes
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log toutes les requêtes avec timing"""
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss / 1024 ** 2

    # Log de la requête entrante
    logger.info(f"📥 {request.method} {request.url.path}")

    response = await call_next(request)

    end_time = time.time()
    end_memory = psutil.Process().memory_info().rss / 1024 ** 2

    # Log de la réponse avec timing
    process_time = (end_time - start_time) * 1000
    logger.info(f"📤 {request.method} {request.url.path} - {response.status_code} ({process_time:.1f}ms)")

    # Logs pour monitoring
    logger.info(f"🔍 {request.url.path} - "
                f"Latency: {process_time:.1f}ms - "
                f"Memory: {end_memory:.1f}MB (+{end_memory - start_memory:.1f}MB)")

    response.headers["X-Process-Time"] = str(process_time)

    return response


# Gestionnaire d'erreurs global
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Gestionnaire d'erreurs global pour debugging"""
    logger.error(f"❌ Erreur non gérée sur {request.url.path}: {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "error": "Erreur interne du serveur",
            "detail": str(exc) if app.debug else "Une erreur inattendue s'est produite",
            "path": str(request.url.path),
            "timestamp": time.time(),
            "service": "semantic-search-spacy"
        }
    )


# Inclusion du router principal
app.include_router(router)


# Endpoint de santé général
@app.get("/health", tags=["health"])
async def health_check():
    """Vérification de l'état général du service"""
    try:
        parser = NLPParsingService()
        transformer = get_query_transformer()

        return {
            "status": "healthy",
            "service": "accord-semantic-search-spacy",
            "version": "2.0.0",
            "timestamp": time.time(),
            "components": {
                "spacy_parser": parser.nlp_model is not None,
                "query_transformer": transformer is not None,
                "patterns_loaded": True
            },
            "performance": {
                "mode": "spacy_patterns_only",
                "expected_latency_ms": "< 100ms"
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "accord-semantic-search-spacy",
                "error": str(e),
                "timestamp": time.time()
            }
        )


# Endpoint racine
@app.get("/", tags=["root"])
async def root():
    """Page d'accueil du service"""
    return {
        "message": "Accord Semantic Search Service",
        "version": "2.0.0",
        "description": "Service de transformation de requêtes en langage naturel utilisant spaCy et patterns enrichis",
        "endpoints": {
            "parse": "/semantic-search/parse",
            "health": "/semantic-search/health",
            "info": "/semantic-search/info",
            "test": "/semantic-search/test-query"
        },
        "docs": "/docs",

    }


# Point d'entrée pour uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )