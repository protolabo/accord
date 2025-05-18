import os
import json
import time
from datetime import datetime

from backend.app.email_providers.google.settings import Config
from backend.app.email_providers.google.gmail_service import GmailService
from backend.app.email_providers.google.gmail_auth import GmailAuthManager
from backend.app.email_providers.google.email_utils import normalize_email_for_storage
from backend.app.services.export_status import update_export_status
from backend.app.services.email_graph.build_graph_main import main as build_graph_main
from backend.app.utils.absolute_path import get_file_path


def classify_exported_emails(output_dir = None):
    """
    Traite tous les fichiers batch exportés pour ajouter les classifications d'emails.

    Args:
        output_dir: Répertoire contenant les fichiers batch
    """
    import os
    import json
    from backend.app.services.ai.pipeline import process_email

    print(f"Classement des emails dans le répertoire: {output_dir}")

    default_output_dir = get_file_path("backend/app/data/mockdata")

    # important pour le test
    if output_dir is None:
        output_dir = default_output_dir

    is_default_directory = (output_dir == default_output_dir)

    if is_default_directory:
        batch_files = [f for f in os.listdir(output_dir) if f == "emails.json"]
    else:
        batch_files = [f for f in os.listdir(output_dir) if f.startswith("emails") and f.endswith(".json")]

    for batch_file in batch_files:
        batch_path = os.path.join(output_dir, batch_file)
        print(f"Traitement du fichier: {batch_file}")

        # Charger le contenu du fichier batch
        with open(batch_path, 'r', encoding='utf-8') as f:
            emails = json.load(f)

        # Classifier chaque email
        total_emails = len(emails)
        for i, email in enumerate(emails):
            if i % 100 == 0:
                print(f"  Progression: {i}/{total_emails} emails traités")

            try:
                classification = process_email({
                    "Subject": email.get("Subject", ""),
                    "Body": {
                        "plain": email.get("Body", {}).get("plain", "")
                    }
                })

                email["accord_main_class"] = classification["main_class"]
                email["accord_sub_classes"] = classification["sub_classes"]

            except Exception as e:
                # Ne rien faire pour l'instant, juste imprimer l'erreur
                print(f"  Erreur lors du classement de l'email {i}: {str(e)}")

        # Réécrire le fichier avec les emails mis à jour
        with open(batch_path, 'w', encoding='utf-8') as f:
            json.dump(emails, f, ensure_ascii=False, indent=2)

        print(f"  Fichier {batch_file} mis à jour avec les classifications")

    print("Classification des emails terminée")


def flowDemarrage(email, max_emails=None, output_dir=None, batch_size=5000):
    """
    Exporte tous les emails de la boîte Gmail vers des fichiers JSON.
    Cette fonction suppose que l'utilisateur est déjà authentifié.

    Args:
        email: Adresse email Gmail
        max_emails: Nombre maximum d'emails à récupérer (None = tous)
        output_dir: Répertoire de sortie
        batch_size: Taille des lots pour l'export

    Returns:
        dict: Métadonnées de l'export ou None en cas d'erreur
    """
    # Mettre à jour le statut - Démarrage du processus
    update_export_status(
        email=email,
        status="processing",
        message="Démarrage du processus d'exportation des emails",
        progress=0
    )

    # Créer les répertoires si nécessaires
    Config.ensure_directories()
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    print(f"Configuration de l'export:")
    print(f"  - Répertoire de sortie: {output_dir}")
    print(f"  - Taille des lots: {batch_size}")
    print(f"  - Nombre max d'emails: {max_emails or 'Tous'}")

    # Initialiser les services nécessaires
    auth_manager = GmailAuthManager()
    gmail_service = GmailService()
    user_id = normalize_email_for_storage(email)

    # Vérifier simplement si l'utilisateur est authentifié
    if not auth_manager.is_authenticated(user_id):
        error_message = f"L'utilisateur {email} n'est pas authentifié. L'exportation ne peut pas continuer."
        print(error_message)
        update_export_status(
            email=email,
            status="error",
            message=error_message,
            progress=0
        )
        return None

    print(f"L'utilisateur {email} est authentifié. Poursuite de l'exportation.")

    update_export_status(
        email=email,
        status="processing",
        message="Récupération des emails en cours...",
        progress=20
    )

    try:
        print(f"Récupération des emails de {email}...")
        start_time = time.time()

        # Récupération des emails
        emails = gmail_service.fetch_all_emails(user_id, max_results=max_emails, batch_size=batch_size)

        # Export des emails par lots
        total_emails = len(emails)
        print(f"Total: {total_emails} emails récupérés en {time.time() - start_time:.2f} secondes")

        export_start_time = time.time()
        print(f"Export des emails vers JSON...")

        # Créer les fichiers batch
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

        update_export_status(
            email=email,
            status="processing",
            message=f"Exportation des emails, {total_emails} emails récupérés",
            progress=50
        )

        print(f"Export terminé en {time.time() - export_start_time:.2f} secondes")
        print(f"Tous les emails ont été exportés vers: {output_dir}")

        # Classification des emails
        print("\nLancement de la classification des emails...")
        try:
            update_export_status(
                email=email,
                status="processing",
                message="Classification des emails en cours...",
                progress=70
            )

            # En production
            if output_dir != get_file_path("backend/app/data/mockdata"):
                classify_exported_emails(output_dir)
            else:
                # En test, utiliser les données de test
                classify_exported_emails()

            print("Classification des emails terminée avec succès ✅")
        except Exception as e:
            print(f"\nErreur lors de la classification des emails: {str(e)}")
            import traceback
            traceback.print_exc()
            raise  # Propager l'erreur pour la gestion globale

        # Construction du graphe
        print("\nLancement de la construction du graphe...")
        try:
            update_export_status(
                email=email,
                status="processing",
                message="Construction du graphe en cours...",
                progress=85
            )

            # En production
            if output_dir != get_file_path("backend/app/data/mockdata"):
                build_graph_main(input_dir=output_dir,
                                 output_dir=get_file_path("backend/app/data/mockdata/graph"),
                                 central_user=email)
            else:
                # En test
                build_graph_main()

            print("Construction du graphe terminée avec succès ✅")
        except Exception as e:
            print(f"\nErreur lors de la construction du graphe: {str(e)}")
            import traceback
            traceback.print_exc()
            raise  # Propager l'erreur pour la gestion globale

        # Mise à jour du statut final
        update_export_status(
            email=email,
            status="completed",
            message="Exportation, classification et construction du graphe terminées avec succès!",
            progress=100,
            extra_data=index
        )

        return index

    except Exception as e:
        print(f"Erreur lors de l'export des emails: {str(e)}")
        import traceback
        traceback.print_exc()
        update_export_status(
            email=email,
            status="error",
            message=f"Erreur pendant le processus: {str(e)}",
            progress=0
        )
        return None

