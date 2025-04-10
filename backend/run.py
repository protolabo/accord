#!/usr/bin/env python

"""
Script de lancement du serveur backend Accord.
Ce script démarre le serveur FastAPI avec Uvicorn.

Options disponibles:
- --host: Adresse de l'hôte (défaut: 0.0.0.0)
- --port: Port d'écoute (défaut: 8000)
- --reload: Active le rechargement automatique du code en cas de modification
- --log-level: Définit le niveau de journalisation
- --env: Définit l'environnement d'exécution (dev, test, prod)
- --config: Spécifie un fichier de configuration personnalisé
- --version: Affiche la version du serveur et quitte
"""

import uvicorn
import argparse
import os
import sys
from dotenv import load_dotenv

# Version du serveur
VERSION = "1.0.0"

def load_environment_variables(env_file=None):
    """Charge les variables d'environnement depuis le fichier .env approprié"""
    if env_file and os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"Configuration chargée depuis {env_file}")
    else:
        load_dotenv()
        print("Configuration chargée depuis le fichier .env par défaut")

def main():
    parser = argparse.ArgumentParser(description="Démarre le serveur backend Accord")
    parser.add_argument("--host", default="0.0.0.0", help="Adresse de l'hôte (défaut: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port (défaut: 8000)")
    parser.add_argument("--reload", action="store_true", help="Activer le rechargement automatique du code")
    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error", "critical"], 
                        help="Niveau de journalisation (défaut: info)")
    parser.add_argument("--env", default="dev", choices=["dev", "test", "prod"], 
                        help="Environnement d'exécution (défaut: dev)")
    parser.add_argument("--config", help="Chemin vers un fichier de configuration personnalisé")
    parser.add_argument("--version", action="store_true", help="Affiche la version et quitte")

    args = parser.parse_args()
    
    # Afficher la version et quitter si demandé
    if args.version:
        print(f"Accord Backend v{VERSION}")
        sys.exit(0)
    
    # Charger les variables d'environnement
    env_file = args.config
    if not env_file and args.env != "dev":
        env_file = f".env.{args.env}"
    
    load_environment_variables(env_file)
    
    # Ajuster les paramètres selon l'environnement
    if args.env == "prod" and args.reload:
        print("ATTENTION: Le rechargement automatique est activé en environnement de production")
    
    print(f"Démarrage du serveur en mode {args.env} sur {args.host}:{args.port}")
    
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