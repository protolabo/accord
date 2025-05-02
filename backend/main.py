import uvicorn
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware


import sys
from backend.app.utils.killer_process import kill_processes_on_port
import secrets
from backend.app.utils.delete_token_file import delete_token_file
from backend.app.routes.auth_routes import router as auth_router
from backend.app.routes.exportmail import router as export_router
from backend.app.routes import mock_data
from backend.app.routes.deconnexion import router as logout_router
from backend.app.routes import emails


app = FastAPI()

# Configuration CORS correcte - DOIT être avant les autres middlewares et avant d'inclure les routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, remplacez par les origines spécifiques
    allow_credentials=True,
    allow_methods=["*"],  # Autoriser toutes les méthodes HTTP, y compris OPTIONS
    allow_headers=["*"],  # Autoriser tous les headers HTTP
    expose_headers=["*"],
    max_age=600,  # Durée de validité du préflight en secondes
)

SECRET_KEY = secrets.token_hex(16)

# Configuration du middleware de session
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="accord_session",
    max_age=1800
)

# Inclure les routers après la configuration des middlewares
app.include_router(auth_router)
app.include_router(export_router)

app.include_router(logout_router)
app.include_router(mock_data.router)
app.include_router(emails.router)




@app.get("/")
async def root():
    return {"message": "API Accord opérationnelle", "status": "ok"}

if __name__ == "__main__":
    if kill_processes_on_port(8000):
        print("Port 8000 is now available...")
        print("Starting FastAPI server with CORS enabled...")

        #delete_token_file()

        uvicorn.run(app, host="0.0.0.0", port=8000)

    else:
        print("Failed to free port 8000")
        sys.exit(1)