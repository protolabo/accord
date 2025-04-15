import os
import pickle
import json
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import requests

# Correction de l'importation pour utiliser le chemin relatif correct
from app.email_providers.google.settings import (
    GOOGLE_CREDENTIALS_PATH,
    TOKEN_DIR,
    GOOGLE_SCOPES,
    OAUTH_REDIRECT_URI
)

class GmailAuthManager:
    """Classe pour gérer l'authentification Gmail"""
    
    def __init__(self, credentials_path=None, tokens_dir=None):
        """
        Initialise le gestionnaire d'authentification Gmail.
        
        Args:
            credentials_path (str): Chemin vers le fichier de credentials Google
            token_dir (str): Répertoire pour stocker les tokens
        """
        self.credentials_path = credentials_path or GOOGLE_CREDENTIALS_PATH
        self.tokens_dir = tokens_dir or TOKEN_DIR
        self.scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.compose',
            'https://www.googleapis.com/auth/gmail.modify',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile'
        ]
        os.makedirs(self.tokens_dir, exist_ok=True)

    def is_authenticated(self, user_id):
        """
        Vérifie si un utilisateur est authentifié.
        
        Args:
            user_id (str): L'identifiant de l'utilisateur
            
        Returns:
            bool: True si l'utilisateur est authentifié, False sinon
        """
        token_path = os.path.join(self.tokens_dir, f"{user_id}.json")
        if not os.path.exists(token_path):
            return False
        
        try:
            with open(token_path, 'r') as token_file:
                credentials = Credentials.from_authorized_user_info(
                    json.load(token_file), self.scopes)
                
            return credentials.valid or (credentials.expired and credentials.refresh_token)
        except Exception:
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

    def exchange_code_for_tokens(self, code):
        """
        Échange le code d'autorisation contre des tokens d'accès.
        
        Args:
            code (str): Le code d'autorisation retourné par Google
            
        Returns:
            dict: Les tokens d'accès et de rafraîchissement
        """
        flow = Flow.from_client_secrets_file(
            self.credentials_path,
            scopes=self.scopes,
            redirect_uri='http://localhost:8000/api/auth/gmail/callback'
        )
        
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        return {
            'access_token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'expires_in': credentials.expiry.timestamp() - flow._clock()
        }
    
    def get_user_info(self, access_token):
        """
        Récupère les informations de l'utilisateur à partir du token d'accès.
        
        Args:
            access_token (str): Le token d'accès
            
        Returns:
            dict: Les informations de l'utilisateur
        """
        response = requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        response.raise_for_status()
        user_info = response.json()
        
        return {
            'id': user_info.get('sub'),
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'picture': user_info.get('picture')
        }
    
    def refresh_access_token(self, refresh_token):
        """
        Rafraîchit le token d'accès en utilisant le token de rafraîchissement.
        
        Args:
            refresh_token (str): Le token de rafraîchissement
            
        Returns:
            dict: Les nouveaux tokens
        """
        with open(self.credentials_path, 'r') as f:
            client_config = json.load(f)
        
        client_id = client_config['installed']['client_id']
        client_secret = client_config['installed']['client_secret']
        
        response = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'client_id': client_id,
                'client_secret': client_secret,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token'
            }
        )
        response.raise_for_status()
        token_data = response.json()
        
        return {
            'access_token': token_data.get('access_token'),
            'expires_in': token_data.get('expires_in')
        }

    def save_tokens(self, user_id, tokens):
        """
        Sauvegarde les tokens pour un utilisateur.
        
        Args:
            user_id (str): L'identifiant de l'utilisateur
            tokens (dict): Les tokens à sauvegarder
        """
        token_path = os.path.join(self.tokens_dir, f"{user_id}.json")
        with open(token_path, 'w') as token_file:
            json.dump(tokens, token_file)
    
    def load_tokens(self, user_id):
        """
        Charge les tokens d'un utilisateur.
        
        Args:
            user_id (str): L'identifiant de l'utilisateur
            
        Returns:
            dict: Les tokens chargés ou None si non trouvés
        """
        token_path = os.path.join(self.tokens_dir, f"{user_id}.json")
        if not os.path.exists(token_path):
            return None
        
        with open(token_path, 'r') as token_file:
            return json.load(token_file)