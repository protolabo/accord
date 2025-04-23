import os
import json
from datetime import datetime
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from backend.app.email_providers.google.settings import Config



# classe pour l'authentification Gmail
class GmailAuthManager:

    def __init__(self, credentials_path=None, tokens_dir=None):
        """
        Args:
            credentials_path (str): Chemin vers le fichier de credentials Google
            tokens_dir (str): Répertoire pour stocker les tokens
        """
        self.credentials_path = credentials_path or Config.GOOGLE_CREDENTIALS_PATH
        self.tokens_dir = tokens_dir or Config.TOKEN_DIR
        self.scopes = Config.GOOGLE_SCOPES

        # Créer les répertoires nécessaires
        os.makedirs(self.tokens_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.credentials_path), exist_ok=True)

    def is_authenticated(self, user_id):
        """
        Args:
            user_id (str): L'identifiant de l'utilisateur

        Returns:
            bool: True si l'utilisateur est authentifié, False sinon
        """
        credentials = self.get_credentials(user_id)
        return credentials is not None and (credentials.valid or
                                            (credentials.expired and credentials.refresh_token))

    def get_auth_url(self, user_id):
        """
        Génère l'URL d'authentification Google pour un utilisateur.

        Args:
            user_id (str): L'identifiant de l'utilisateur

        Returns:
            str: L'URL d'authentification
        """
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path, self.scopes)


            flow.redirect_uri = "http://localhost:8000/auth/callback"

            auth_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent',
                state=user_id
            )

            # Sauvegarder la configuration
            flow_config = {
                'client_id': flow.client_config['client_id'],
                'client_secret': flow.client_config['client_secret'],
                'redirect_uri': flow.redirect_uri,
                'scopes': self.scopes,
                'state': state
            }

            flow_path = os.path.join(self.tokens_dir, f"{user_id}_flow.json")
            with open(flow_path, 'w') as token_file:
                json.dump(flow_config, token_file)

            return auth_url

        except Exception as e:
            print(f"Erreur lors de la génération de l'URL d'authentification: {str(e)}")
            raise

    def handle_callback(self, code, state):
        """
        Args:
            code (str): Le code d'autorisation retourné par Google
            state (str): L'état passé lors de la génération de l'URL

        Returns:
            dict: Les informations de l'utilisateur authentifié
        """
        user_id = state
        flow_path = os.path.join(self.tokens_dir, f"{user_id}_flow.json")

        try:
            # Charger la configuration
            with open(flow_path, 'r') as file:
                flow_config = json.load(file)

            # Créer un nouveau flow avec la configuration sauvegardée
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path,
                scopes=flow_config['scopes']
            )
            flow.redirect_uri = flow_config['redirect_uri']

            # Échanger le code contre des credentials
            flow.fetch_token(code=code)
            credentials = flow.credentials

            # Sauvegarder les credentials
            self._save_credentials(user_id, credentials)

            # Nettoyer le fichier temporaire
            if os.path.exists(flow_path):
                os.remove(flow_path)

            # Obtenir les informations de l'utilisateur
            service = build('gmail', 'v1', credentials=credentials)
            profile = service.users().getProfile(userId='me').execute()

            return {
                'user_id': user_id,
                'email': profile.get('emailAddress', ''),
                'message': 'Authentification réussie'
            }

        except Exception as e:
            print(f"Erreur lors du traitement du callback: {str(e)}")
            if os.path.exists(flow_path):
                os.remove(flow_path)
            raise

    def get_credentials(self, user_id):
        """
        Args:
            user_id (str): Identifiant de l'utilisateur

        Returns:
            google.oauth2.credentials.Credentials: Objet credentials ou None si non authentifié
        """
        token_path = os.path.join(self.tokens_dir, f"{user_id}.json")
        if not os.path.exists(token_path):
            return None

        try:
            # Charger les credentials
            with open(token_path, 'r') as token_file:
                creds_data = json.load(token_file)

            # Vérifier si les données nécessaires sont présentes
            if not creds_data.get('refresh_token'):
                return None

            # Convertir la date d'expiration
            expiry = None
            if creds_data.get('expiry'):
                expiry = datetime.fromisoformat(creds_data['expiry'])

            # Créer l'objet Credentials
            credentials = Credentials(
                token=creds_data['token'],
                refresh_token=creds_data['refresh_token'],
                token_uri=creds_data['token_uri'],
                client_id=creds_data['client_id'],
                client_secret=creds_data['client_secret'],
                scopes=creds_data['scopes'],
                expiry=expiry
            )

            # Rafraîchir si nécessaire
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                self._save_credentials(user_id, credentials)

            return credentials

        except Exception as e:
            print(f"Erreur lors de la récupération des credentials: {str(e)}")
            return None

    def _save_credentials(self, user_id, credentials):
        """
        Args:
            user_id (str): Identifiant de l'utilisateur
            credentials (Credentials): Objet credentials à sauvegarder
        """
        token_path = os.path.join(self.tokens_dir, f"{user_id}.json")

        creds_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None
        }

        with open(token_path, 'w') as token_file:
            json.dump(creds_data, token_file)