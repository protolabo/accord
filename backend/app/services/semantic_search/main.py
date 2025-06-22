"""
Point d'entrée FastAPI pour le service de recherche sémantique Accord.
Configure l'application avec tous les endpoints et middlewares nécessaires.

🎯 Résultat

Cas simple : spaCy seul (rapide)
Cas complexe : spaCy + LLM fusionnés (qualité)

"""
import time
import logging
from contextlib import asynccontextmanager

import psutil
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

debuguerBreakpoint = True
from backend.app.services.semantic_search.endpoints import router
from backend.app.services.semantic_search.llm_engine import get_query_parser
from backend.app.services.semantic_search.query_transformer import get_query_transformer

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

debuguerBreakpoint = True
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire de cycle de vie de l'application"""

    # Startup
    logger.info("🚀 Démarrage du service de recherche sémantique Accord")

    # Pré-chargement des modèles pour optimiser les premières requêtes
    logger.info("📥 Pré-chargement des composants...")

    try:
        # Initialiser le parser LLM
        debuguerBreakpoint = True
        llm_parser = get_query_parser()
        if llm_parser.model:
            logger.info("✅ Modèle LLM Mistral 7B chargé")
        else:
            logger.warning("⚠️ Modèle LLM non disponible, fallback activé")

        # Initialiser le transformer
        transformer = get_query_transformer()
        logger.info("✅ Query transformer initialisé")

        # Test de sanité au demarrage
        """
            - Vérifier que le pipeline complet fonctionne (LLM + transformer)
            - Mesurer les performances au démarrage
            - S'assurer que tous les composants sont correctement chargés
        """
        test_query = "emails de test"
        start_time = time.time()
        from backend.app.services.semantic_search.models import NaturalLanguageRequest
        # crée un objet Pydantic pour encapsuler la requête,
        test_request = NaturalLanguageRequest(query=test_query)
        debuguerBreakpoint = True
        result = transformer.transform_query(test_request) #Go to : query_transformer.transform_query
        print(result)


        test_time = (time.time() - start_time) * 1000
        logger.info(f"✅ Test de sanité réussi en {test_time:.1f}ms")

    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation: {e}")
    logger.info("🎯 Service de recherche sémantique prêt")

    yield

    # Shutdown
    logger.info("🛑 Arrêt du service de recherche sémantique")


# Création de l'application FastAPI
app = FastAPI(
    title="Accord Semantic Search Service",
    description="Service de recherche sémantique pour l'application Accord - Transforme le langage naturel en requêtes structurées",
    version="1.0.0",
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
    process_time = (time.time() - start_time) * 1000
    logger.info(f"📤 {request.method} {request.url.path} - {response.status_code} ({process_time:.1f}ms)")

    # Logs pour monitoring
    logger.info(f"🔍 {request.url.path} - "
                f"Latency: {(end_time - start_time) * 1000:.1f}ms - "
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
            "timestamp": time.time()
        }
    )


# Inclusion du router principal
app.include_router(router)




# Point d'entrée pour uvicorn
if __name__ == "__main__":
    import uvicorn

    debuguerBreakpoint = True
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )