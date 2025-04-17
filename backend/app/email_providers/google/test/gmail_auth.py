# test_gmail_auth.py
import os
import webbrowser
import time
from backend.app.email_providers.google.gmail_auth import GmailAuthManager
from backend.app.tasks.email_processor import EmailProcessor, normalize_email_for_storage
from backend.app.email_providers.google.settings import *


def main():
    # Instancier les services
    auth_manager = GmailAuthManager(GOOGLE_CREDENTIALS_PATH, TOKEN_DIR)
    email_processor = EmailProcessor(GOOGLE_CREDENTIALS_PATH, TOKEN_DIR, OUTPUT_DIR)

    # Email de test
    test_email = "johndoe@gmail.com"
    user_id = normalize_email_for_storage(test_email)
    print(f"User ID: {user_id}")

    # Vérification de l'authentification avec gestion complète
    print("Vérification de l'authentification...")
    is_auth = auth_manager.is_authenticated(user_id)

    if not is_auth:
        print("Non authentifié. Génération de l'URL d'authentification...")
        auth_url = auth_manager.get_auth_url(user_id)

        print("\n=================================================")
        print("IMPORTANT: Votre serveur FastAPI doit être démarré!")
        print("Exécutez 'python -m backend.main' dans un autre terminal")
        print("=================================================\n")

        print(f"URL d'authentification: {auth_url}")

        # Proposer d'ouvrir l'URL automatiquement ou manuellement
        print("\nQue souhaitez-vous faire?")
        print("1. Ouvrir l'URL dans votre navigateur automatiquement")
        print("2. Copier l'URL et l'ouvrir manuellement")
        choice = input("Choix (1/2): ")

        if choice == "1":
            print("\nOuverture du navigateur...")
            webbrowser.open(auth_url)

        print("\nSuivez les étapes dans le navigateur pour vous authentifier avec Google.")
        print("Une fois l'authentification terminée, vous serez redirigé vers votre application.")
        print("\nAppuyez sur Entrée une fois l'authentification terminée pour continuer...")
        input()

        # Laisser un peu de temps pour que les fichiers soient correctement écrits
        print("Pause pour finaliser l'authentification...")
        time.sleep(2)

        # Vérification après authentification
        is_auth = auth_manager.is_authenticated(user_id)

    if is_auth:
        print("Authentification réussie...✅")
        print(f"L'utilisateur {test_email} est maintenant authentifié.")

        # Décommenter pour tester le traitement des emails
        # print("Authentifié ! Traitement des emails...")
        # result = email_processor.process_user_emails(test_email, max_results=10)
        # print(f"Résultat: {result}")
    else:
        print("Échec de l'authentification après le processus.")
        print("Vérifiez que:")
        print("1. Votre serveur FastAPI est bien démarré")
        print("2. Vous avez complété toutes les étapes d'authentification dans le navigateur")
        print("3. Vous avez été correctement redirigé vers la page de succès")


if __name__ == "__main__":
    main()