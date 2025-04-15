from backend.app.email_providers.google.gmail_service import GmailService
from backend.app.email_providers.google.email_storage import EmailStorage

import os

def normalize_email_for_storage(email):
    """Convertit une adresse email en un identifiant sécurisé pour le stockage."""
    return email.replace('@', '_at_').replace('.', '_dot_')

class EmailProcessor:
    def __init__(self, credentials_path, tokens_dir, output_dir="collected_data"):
        self.gmail_service = GmailService(credentials_path, tokens_dir)
        self.storage = EmailStorage(storage_dir=output_dir)
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        #self.email_graph = EmailGraphBuilder()
        #self.email_classifier = EmailClassifier()

    async def process_user_emails(self, email_address, max_results=None):

        # Convertir l'email en identifiant pour le stockage
        user_id = normalize_email_for_storage(email_address)

        # Étape 0: Vérification de l'authentification
        print(f"Vérification de l'authentification pour {email_address}")

        # Méthode explicite de vérification d'authentification
        is_authenticated = self._is_user_authenticated(user_id)

        if not is_authenticated:
            auth_url = self.gmail_service.auth_manager.get_auth_url(user_id)
            print(f"⚠️ L'utilisateur {email_address} doit s'authentifier via l'URL:")
            print(auth_url)
            return {
                "status": "authentication_required",
                "auth_url": auth_url
            }

        print(f"✅ Utilisateur {email_address} authentifié.")

        # Étape 1: Récupération des emails
        try:
            print(f"Étape 1: Récupération des emails pour {email_address}")

            # Récupérer les emails
            emails = self.gmail_service.fetch_all_emails(user_id, max_results=max_results)
            print(f"✅ {len(emails)} emails récupérés")

            if not emails:
                return {
                    "status": "success",
                    "message": "Aucun email à traiter",
                    "email_count": 0
                }

            emails_with_owner = []
            for email in emails:
                email["owner_email"] = email_address
                emails_with_owner.append(email)

            # Étape 2: Stockage temporaire
            print("Étape 2: Stockage temporaire des emails")

            # Utiliser le stockage JSON sécurisé
            self.storage.save_emails(user_id, emails_with_owner)
            print("✅ Emails stockés temporairement")

            # Étape 3: Construction du graphe de connexion
            # Étape 4: classification de mails
            # Étape 5: Generation de threads
            # Étape 6: Stockage des structures intelligentes
            # Étape 7: Nettoyage des données brutes

            return {
                "status": "success",
                "message": f"{len(emails)} emails récupérés et stockés pour {email_address}",
                "email_count": len(emails),
            }

        except Exception as e:
            print(f"❌ Erreur lors du traitement des emails: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

    def _is_user_authenticated(self, user_id):
        """Vérifie si l'utilisateur est authentifié de manière robuste.

        Args:
            user_id: Identifiant de l'utilisateur

        Returns:
            bool: True si l'utilisateur est authentifié, False sinon
        """
        try:
            # Tente d'obtenir le service pour vérifier l'authentification
            service = self.gmail_service.get_service(user_id)
            # Effectue un appel léger pour vérifier que les credentials fonctionnent
            profile = service.users().getProfile(userId='me').execute()
            print (f"profil utilisateur : {profile}")
            return True
        except Exception as e:
            print(f"Utilisateur non authentifié: {str(e)}")
            return False