# Chemin du fichier: backend/app/scripts/export_gmail_to_json.py

import os
import json
import time
import argparse
from datetime import datetime
from pathlib import Path

# Import des services Gmail existants
from backend.app.email_providers.google.gmail_service import GmailService
from backend.app.email_providers.google.gmail_auth import GmailAuthManager
from backend.app.services.mail_graph.utils.json_serializer import save_component_to_json


def normalize_email_for_storage(email):
    """Normalise l'adresse email pour l'utiliser comme identifiant."""
    if not email:
        return ""
    return email.lower().strip().replace("@", "_at_").replace(".", "_dot_")


def export_emails_to_json(email="samsungs2.hn63@gmail.com", max_emails=None, output_dir=None, batch_size=1000):
    """
    Exporte tous les emails de la boîte Gmail vers des fichiers JSON.

    Args:
        email: Adresse email Gmail
        max_emails: Nombre maximum d'emails à récupérer (None = tous)
        output_dir: Répertoire de sortie
        batch_size: Taille des lots pour l'export

    Returns:
        dict: Métadonnées de l'export
    """

    # Configuration des chemins
    credentials_path = os.environ.get(
        "GOOGLE_CREDENTIALS_PATH",
        "C:\\Users\\herve\\OneDrive - Universite de Montreal\\Github\\accord\\backend\\app\\email_providers\\google\\credentials"
    )

    tokens_dir = os.environ.get(
        "GOOGLE_TOKEN_DIR",
        "C:\\Users\\herve\\OneDrive - Universite de Montreal\\Github\\accord\\backend\\app\\email_providers\\google\\secure_storage\\tokens"
    )

    if not output_dir:
        # Répertoire par défaut avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(os.path.dirname(__file__), f"../../../data/emails_export_{timestamp}")

    os.makedirs(output_dir, exist_ok=True)

    print(f"Configuration de l'export:")
    print(f"  - Email: {email}")
    print(f"  - Fichier credentials: {credentials_path}")
    print(f"  - Répertoire tokens: {tokens_dir}")
    print(f"  - Répertoire de sortie: {output_dir}")
    print(f"  - Taille des lots: {batch_size}")
    print(f"  - Nombre max d'emails: {max_emails or 'Tous'}")

    # Initialisation des services
    auth_manager = GmailAuthManager(credentials_path, tokens_dir)
    gmail_service = GmailService(credentials_path, tokens_dir)

    # Normalisation de l'email pour l'ID utilisateur
    user_id = normalize_email_for_storage(email)

    # Vérification de l'authentification
    if not auth_manager.is_authenticated(user_id):
        print("L'utilisateur n'est pas authentifié. Veuillez exécuter le script d'authentification.")
        print("Exemple: python -m backend.app.email_providers.google.test.test_gmail_auth")
        return None

    # Récupération des emails
    print(f"Récupération des emails de {email}...")
    start_time = time.time()

    try:
        emails = gmail_service.fetch_all_emails(user_id, max_results=max_emails, batch_size=batch_size)

        # Regrouper les emails par lots pour l'export
        total_emails = len(emails)
        print(f"Total: {total_emails} emails récupérés en {time.time() - start_time:.2f} secondes")

        # Export par lots
        export_start_time = time.time()
        print(f"Export des emails vers JSON...")

        for i in range(0, total_emails, batch_size):
            batch_num = (i // batch_size) + 1
            end_idx = min(i + batch_size, total_emails)
            batch_emails = emails[i:end_idx]

            batch_file = os.path.join(output_dir, f"emails_batch_{batch_num}.json")
            print(f"Écriture du lot {batch_num} ({len(batch_emails)} emails) vers {batch_file}")

            with open(batch_file, 'w', encoding='utf-8') as f:
                json.dump(batch_emails, f, ensure_ascii=False, indent=2)

        # Création d'un fichier index
        index = {
            "email": email,
            "user_id": user_id,
            "total_emails": total_emails,
            "total_batches": (total_emails + batch_size - 1) // batch_size,
            "max_emails": max_emails,
            "export_date": datetime.now().isoformat(),
            "batches": [f"emails_batch_{i + 1}.json" for i in range((total_emails + batch_size - 1) // batch_size)],
            "duration_seconds": time.time() - start_time
        }

        index_file = os.path.join(output_dir, "index.json")
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

        print(f"Export terminé en {time.time() - export_start_time:.2f} secondes")
        print(f"Tous les emails ont été exportés vers: {output_dir}")
        print(f"Fichier index créé: {index_file}")

        return index

    except Exception as e:
        print(f"Erreur lors de l'export des emails: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Fonction principale exécutée lorsque le script est lancé directement."""
    parser = argparse.ArgumentParser(description='Exporte les emails Gmail vers des fichiers JSON.')

    parser.add_argument('--email', type=str,
                        help='Adresse email Gmail')

    parser.add_argument('--output-dir', type=str, default=None,
                        help='Répertoire de sortie pour les fichiers JSON')

    parser.add_argument('--max-emails', type=int, default=None,
                        help='Nombre maximum d\'emails à récupérer (par défaut: tous)')

    parser.add_argument('--batch-size', type=int, default=1000,
                        help='Taille des lots pour l\'export (par défaut: 1000)')

    args = parser.parse_args()

    export_emails_to_json(
        email=args.email,
        max_emails=args.max_emails,
        output_dir=args.output_dir,
        batch_size=args.batch_size
    )


if __name__ == "__main__":
    main()