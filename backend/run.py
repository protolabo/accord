#!/usr/bin/env python

"""
Script de lancement du serveur backend Accord.
Ce script démarre le serveur FastAPI avec Uvicorn.
"""

import uvicorn
import argparse
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Démarre le serveur backend Accord")
    parser.add_argument("--host", default="0.0.0.0", help="Adresse de l'hôte (défaut: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port (défaut: 8000)")
    parser.add_argument("--reload", action="store_true", help="Activer le rechargement automatique du code")
    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error", "critical"], 
                        help="Niveau de journalisation (défaut: info)")

    args = parser.parse_args()

    # Configurer et lancer le serveur Uvicorn
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    )

if __name__ == "__main__":
    main()