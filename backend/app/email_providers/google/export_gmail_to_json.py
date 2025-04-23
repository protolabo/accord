import os
import json
import time
import argparse
import webbrowser
from datetime import datetime

from backend.app.email_providers.google.settings import Config
from backend.app.email_providers.google.gmail_service import GmailService
from backend.app.email_providers.google.gmail_auth import GmailAuthManager
from backend.app.email_providers.google.email_utils import normalize_email_for_storage


def export_emails_to_json(email, max_emails=None, output_dir=None, batch_size=5000):
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
    # Créer les répertoires si nécessaires
    Config.ensure_directories()
    os.makedirs(output_dir, exist_ok=True)

    print(f"Configuration de l'export:")
    print(f"  - Répertoire de sortie: {output_dir}")
    print(f"  - Taille des lots: {batch_size}")
    print(f"  - Nombre max d'emails: {max_emails or 'Tous'}")

    auth_manager = GmailAuthManager()
    gmail_service = GmailService()

    user_id = normalize_email_for_storage(email)

    # Vérification de l'authentification avec retry limité
    max_auth_attempts = 3
    auth_attempts = 0
    is_authenticated = False

    while not is_authenticated and auth_attempts < max_auth_attempts:
        auth_attempts += 1

        if not auth_manager.is_authenticated(user_id):
            print(f"Tentative d'authentification {auth_attempts}/{max_auth_attempts}...")
            auth_url = auth_manager.get_auth_url(user_id)
            print(f"URL d'authentification: {auth_url}")
            webbrowser.open(auth_url)
            print("\nSuivez les étapes dans le navigateur pour vous authentifier avec Google.")
            print("Une fois l'authentification terminée, vous serez redirigé vers votre application.")
            print("\nAppuyez sur Entrée une fois l'authentification terminée pour continuer...")
            input()

            # Laisser un peu de temps pour que les fichiers soient correctement écrits
            time.sleep(2)

            is_authenticated = auth_manager.is_authenticated(user_id)
            if is_authenticated:
                print("Authentification réussie...✅")
                print(f"L'utilisateur {email} est maintenant authentifié.")
            else:
                print("L'authentification a échoué. Veuillez réessayer.")
        else:
            is_authenticated = True
            print(f"L'utilisateur {email} est déjà authentifié.")

    if not is_authenticated:
        print(f"Échec de l'authentification après {max_auth_attempts} tentatives.")
        return None

    # Récupération des emails
    print(f"Récupération des emails de {email}...")
    start_time = time.time()

    try:
        emails = gmail_service.fetch_all_emails(user_id, max_results=max_emails, batch_size=batch_size)

        # Export des emails par lots
        total_emails = len(emails)
        print(f"Total: {total_emails} emails récupérés en {time.time() - start_time:.2f} secondes")

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


        print(f"Export terminé en {time.time() - export_start_time:.2f} secondes")
        print(f"Tous les emails ont été exportés vers: {output_dir}")

        return index

    except Exception as e:
        print(f"Erreur lors de l'export des emails: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


