# test_web_auth_flow.py
import webbrowser
import os
import uuid
from backend.app.email_providers.google.gmail_auth import GmailAuthManager
from backend.app.email_providers.google.settings import GOOGLE_CREDENTIALS_PATH, TOKEN_DIR


def main():
    # Instanciation du gestionnaire d'authentification
    auth_manager = GmailAuthManager(GOOGLE_CREDENTIALS_PATH, TOKEN_DIR)

    # Génération d'un ID temporaire
    temp_id = str(uuid.uuid4())
    user_id = f"temp_{temp_id}"
    print(f"ID temporaire généré: {user_id}")

    # Génération de l'URL d'authentification
    print("Génération de l'URL d'authentification...")
    auth_url = auth_manager.get_auth_url(user_id)

    # Instructions pour l'utilisateur
    print("\n=================================================")
    print("IMPORTANT: Votre serveur FastAPI doit être démarré!")
    print("Exécutez 'python -m backend.main' dans un autre terminal")
    print("=================================================\n")

    print(f"URL d'authentification: {auth_url}")
    print("\nQue souhaitez-vous faire?")
    print("1. Ouvrir l'URL dans votre navigateur")
    print("2. Copier l'URL et l'ouvrir manuellement")
    choice = input("Choix (1/2): ")

    if choice == "1":
        print("\nOuverture du navigateur...")
        webbrowser.open(auth_url)

    print("\nSuivez les étapes dans le navigateur pour vous authentifier.")
    print("Après l'authentification, vous serez redirigé vers votre application.")
    print("\nUne fois l'authentification terminée, appuyez sur Entrée pour vérifier le statut.")
    input()

    # Vérification de l'authentification
    is_auth = auth_manager.is_authenticated(user_id)
    if is_auth:
        print(f"\nAuthentification réussie pour l'ID temporaire: {user_id} ✅")
        print("Vous pouvez utiliser cet ID pour des tests futurs.")

        # Sauvegarde de l'ID pour usage futur
        with open("dernier_id_auth.txt", "w") as f:
            f.write(user_id)
        print("ID sauvegardé dans 'dernier_id_auth.txt'")
    else:
        print("\nL'authentification a échoué ou n'est pas encore terminée.")
        print("Assurez-vous de terminer le processus d'authentification dans le navigateur.")


if __name__ == "__main__":
    main()