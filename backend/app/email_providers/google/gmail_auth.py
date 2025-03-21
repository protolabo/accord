import os
import pickle
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta


from settings import (
    GOOGLE_CREDENTIALS_PATH,
    TOKEN_DIR,
    GOOGLE_SCOPES,
    OAUTH_REDIRECT_URI
)

class GmailAuthManager:
    """Gestionnaire d'authentification pour l'API Gmail."""

    def __init__(self, credentials_path=None, tokens_dir=None):
        """
        Initialise le gestionnaire d'authentification.

        Args:
            credentials_path: Chemin vers le fichier client_secret.json. Si None, utilise la valeur de configuration.
            tokens_dir: Répertoire pour stocker les jetons d'authentification. Si None, utilise la valeur de configuration.
        """
        # Utilisation des paramètres de configuration avec possibilité de surcharge
        self.credentials_path = credentials_path or GOOGLE_CREDENTIALS_PATH
        self.tokens_dir = tokens_dir or TOKEN_DIR

        # Vérification de l'existence des paramètres nécessaires
        if not self.credentials_path or not os.path.exists(self.credentials_path):
            raise ValueError(f"Le fichier de credentials n'existe pas à l'emplacement: {self.credentials_path}")

        # Créer le répertoire de jetons s'il n'existe pas
        os.makedirs(self.tokens_dir, exist_ok=True)

    def is_authenticated(self, user_id):
        """
        Vérifie si l'utilisateur est authentifié avec des credentials valides.

        Args:
            user_id: Identifiant de l'utilisateur

        Returns:
            bool: True si l'utilisateur est authentifié avec des credentials valides, False sinon
        """
        # Vérifier l'existence des credentials
        token_path = os.path.join(self.tokens_dir, f"{user_id}.json")
        if not os.path.exists(token_path):
            return False

        try:
            # Charger les credentials
            with open(token_path, 'r') as token_file:
                creds_data = json.load(token_file)

            # Vérifier si les données nécessaires sont présentes
            if not creds_data.get('refresh_token'):
                return False

            # Convertir la date d'expiration en objet datetime
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

            # Si les credentials sont expirés, essayer de les rafraîchir
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())

                # Mettre à jour le fichier avec les nouveaux credentials
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

            # Faire un appel léger à l'API pour vérifier que les credentials fonctionnent
            service = build('gmail', 'v1', credentials=credentials)
            service.users().getProfile(userId='me').execute()

            return True

        except Exception as e:
            print(f"Vérification d'authentification échouée pour l'utilisateur {user_id}: {str(e)}")
            return False

    def get_auth_url(self, user_id):
        """
        Génère l'URL d'authentification Google pour un utilisateur.
        """
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path, GOOGLE_SCOPES)

            # Configuration pour le mode serveur web
            flow.redirect_uri = "http://localhost:8000/auth/callback"

            auth_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent',
                state=user_id
            )

            # Instead of pickling the flow object, store its configuration
            flow_config = {
                'client_id': flow.client_config['client_id'],
                'client_secret': flow.client_config['client_secret'],
                'redirect_uri': flow.redirect_uri,
                'scopes': GOOGLE_SCOPES,
                'state': state
            }

            # Save the configuration instead of the flow object
            flow_path = os.path.join(self.tokens_dir, f"{user_id}_flow.json")
            with open(flow_path, 'w') as token_file:
                json.dump(flow_config, token_file)

            return auth_url

        except Exception as e:
            print(f"Erreur lors de la génération de l'URL d'authentification: {str(e)}")
            raise

    def handle_callback(self, code, state):
        """
        Traite le callback de l'authentification Google.
        """
        user_id = state
        flow_path = os.path.join(self.tokens_dir, f"{user_id}_flow.json")

        try:
            # Load flow configuration
            with open(flow_path, 'r') as file:
                flow_config = json.load(file)

            # Create a new flow with the original client secrets
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path,
                scopes=flow_config['scopes']
            )

            # Set the redirect URI from the stored config
            flow.redirect_uri = flow_config['redirect_uri']

            # Exchange the authorization code for credentials
            flow.fetch_token(code=code)
            credentials = flow.credentials

            # Save credentials for future use
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

            # Clean up temporary flow file
            if os.path.exists(flow_path):
                os.remove(flow_path)

            # Get user information
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
        Récupère les credentials de l'utilisateur.

        Args:
            user_id: Identifiant de l'utilisateur

        Returns:
            google.oauth2.credentials.Credentials: Objet credentials ou None si non authentifié
        """
        # Vérifier l'existence des credentials
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

            # Convertir la date d'expiration en objet datetime
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

            # Si les credentials sont expirés, essayer de les rafraîchir
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())

                # Mettre à jour le fichier avec les nouveaux credentials
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

            return credentials

        except Exception as e:
            print(f"Erreur lors de la récupération des credentials pour l'utilisateur {user_id}: {str(e)}")
            return None