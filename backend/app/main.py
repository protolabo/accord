# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from app.core.config import settings
from app.db.connection import init_db
from app.routes import auth, emails
from backend.app.utils.old_version.old_email_sync import start_email_sync_task

app = FastAPI(
    title="Accord API",
    description="API pour l'application Accord de gestion d'emails",
    version="1.0.0"
)

# Configurer CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifiez les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tâche de synchronisation des emails
email_sync_task = None

# Événement de démarrage pour initialiser la base de données et démarrer les tâches
@app.on_event("startup")
async def startup_db_client():
    # Initialiser la connexion à la base de données
    await init_db()
    
    # Démarrer la tâche de synchronisation des emails en arrière-plan
    global email_sync_task
    email_sync_task = asyncio.create_task(start_email_sync_task())

# Événement d'arrêt pour nettoyer les ressources
@app.on_event("shutdown")
async def shutdown_db_client():
    # Annuler la tâche de synchronisation si elle est en cours
    global email_sync_task
    if email_sync_task:
        email_sync_task.cancel()
        try:
            await email_sync_task
        except asyncio.CancelledError:
            pass

# Inclure les routes
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(emails.router, prefix="/api", tags=["Emails"])

# Route de base pour vérifier que l'API fonctionne
@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Bienvenue sur l'API Accord", "status": "online"}


