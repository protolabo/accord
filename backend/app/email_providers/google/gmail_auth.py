import os
import json
from datetime import datetime
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from backend.app.email_providers.google.settings import Config


# Class for Gmail authentication
class GmailAuthManager:

    def __init__(self, credentials_path=None, tokens_dir=None):
        """
        Args:
            credentials_path (str): Path to Google credentials file
            tokens_dir (str): Directory for storing tokens
        """
        self.credentials_path = credentials_path or Config.GOOGLE_CREDENTIALS_PATH
        self.tokens_dir = tokens_dir or Config.TOKEN_DIR
        self.scopes = Config.GOOGLE_SCOPES

        # Ensure directories exist
        os.makedirs(self.tokens_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.credentials_path), exist_ok=True)

    def is_authenticated(self, user_id):
        """
        Args:
            user_id (str): User identifier

        Returns:
            bool: True if user is authenticated, False otherwise
        """
        credentials = self.get_credentials(user_id)
        return credentials is not None and (credentials.valid or
                                            (credentials.expired and credentials.refresh_token))

    def get_auth_url(self, user_id):
        """
        Generates the Google authentication URL for a user.
        """
        try:
            # Clean up any existing flow files first
            flow_path = os.path.join(self.tokens_dir, f"{user_id}_flow.json")
            if os.path.exists(flow_path):
                try:
                    os.remove(flow_path)
                    print(f"Removed existing flow file: {flow_path}")
                except Exception as e:
                    print(f"Warning: Could not remove existing flow file: {e}")

            # Ensure directories exist with proper error handling
            print(f"Token directory path: {self.tokens_dir}")
            os.makedirs(self.tokens_dir, exist_ok=True)

            # Print current working directory for debugging
            print(f"Current working directory: {os.getcwd()}")

            # Create flow using InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path, self.scopes)

            flow.redirect_uri = "http://localhost:8000/auth/callback"

            # Generate auth URL
            auth_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent',
                state=user_id  # Using user_id as state
            )

            # Create flow configuration
            flow_config = {
                'client_id': flow.client_config['client_id'],
                'client_secret': flow.client_config['client_secret'],
                'redirect_uri': flow.redirect_uri,
                'scopes': self.scopes,
                'state': state
            }

            # Save flow configuration with correct filename format
            # IMPORTANT: Use {user_id}_flow.json to match what handle_callback looks for
            flow_path = os.path.join(self.tokens_dir, f"{user_id}_flow.json")
            print(f"Saving flow configuration to: {flow_path}")

            # Make sure parent directory exists
            os.makedirs(os.path.dirname(flow_path), exist_ok=True)

            with open(flow_path, 'w') as token_file:
                json.dump(flow_config, token_file)

            # Verify the file was created
            if os.path.exists(flow_path):
                print(f"✅ Flow configuration file created successfully at {flow_path}")
            else:
                print(f"❌ Failed to create flow configuration file at {flow_path}")

            return auth_url

        except Exception as e:
            print(f"Error generating authentication URL: {str(e)}")
            # Print the full exception traceback for debugging
            import traceback
            traceback.print_exc()
            raise

    def handle_callback(self, code, state):
        """
        Handle the OAuth callback from Google
        """
        user_id = state
        flow_path = os.path.join(self.tokens_dir, f"{user_id}_flow.json")

        print(f"Looking for flow configuration at: {flow_path}")
        print(f"File exists: {os.path.exists(flow_path)}")

        try:
            # If flow file exists, use it
            if os.path.exists(flow_path):
                with open(flow_path, 'r') as file:
                    flow_config = json.load(file)

                # Create a new flow with the saved configuration
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path,
                    scopes=flow_config['scopes']
                )
                flow.redirect_uri = flow_config['redirect_uri']

                # Exchange the code for credentials
                try:
                    flow.fetch_token(code=code)
                    credentials = flow.credentials

                    # Save the credentials
                    self._save_credentials(user_id, credentials)

                    # Safely clean up the file
                    try:
                        # Just directly remove the file
                        os.remove(flow_path)
                        print(f"Successfully removed flow file: {flow_path}")
                    except Exception as clean_error:
                        print(f"Warning: Could not clean up flow file: {clean_error}")

                    # Get user information
                    service = build('gmail', 'v1', credentials=credentials)
                    profile = service.users().getProfile(userId='me').execute()

                    return {
                        'user_id': user_id,
                        'email': profile.get('emailAddress', ''),
                        'message': 'Authentication successful'
                    }
                except Exception as e:
                    print(f"Error exchanging code for token: {str(e)}")

                    # Handle invalid_grant specifically
                    if "invalid_grant" in str(e):
                        print("IMPORTANT: Authorization code has already been used.")
                        print("The OAuth2 authorization code can only be used once.")

                        # Try to clean up the flow file
                        try:
                            if os.path.exists(flow_path):
                                os.remove(flow_path)
                                print(f"Removed invalid flow file: {flow_path}")
                        except Exception as clean_error:
                            print(f"Warning: Could not clean up flow file: {clean_error}")

                    raise
            else:
                # Fallback for when flow file is not found
                print(f"Flow file not found at {flow_path}. Attempting direct token exchange.")

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path,
                    scopes=self.scopes
                )
                flow.redirect_uri = "http://localhost:8000/auth/callback"

                try:
                    # Try direct token exchange
                    flow.fetch_token(code=code)
                    credentials = flow.credentials

                    # Save credentials
                    self._save_credentials(user_id, credentials)

                    # Get user information
                    service = build('gmail', 'v1', credentials=credentials)
                    profile = service.users().getProfile(userId='me').execute()

                    return {
                        'user_id': user_id,
                        'email': profile.get('emailAddress', ''),
                        'message': 'Authentication successful (direct method)'
                    }
                except Exception as e:
                    print(f"Direct token exchange failed: {str(e)}")
                    if "invalid_grant" in str(e):
                        print("IMPORTANT: This error often means the code was already used once.")
                        print("The OAuth2 authorization code can only be used once.")
                        print("The user may need to restart the authentication process.")
                    raise

        except Exception as e:
            print(f"Error in callback handler: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

    def get_credentials(self, user_id):
        """
        Args:
            user_id (str): User identifier

        Returns:
            google.oauth2.credentials.Credentials: Credentials object or None if not authenticated
        """
        token_path = os.path.join(self.tokens_dir, f"{user_id}.json")
        if not os.path.exists(token_path):
            return None

        try:
            # Load credentials
            with open(token_path, 'r') as token_file:
                creds_data = json.load(token_file)

            # Verify required data is present
            if not creds_data.get('refresh_token'):
                return None

            # Convert expiration date
            expiry = None
            if creds_data.get('expiry'):
                expiry = datetime.fromisoformat(creds_data['expiry'])

            # Create Credentials object
            credentials = Credentials(
                token=creds_data['token'],
                refresh_token=creds_data['refresh_token'],
                token_uri=creds_data['token_uri'],
                client_id=creds_data['client_id'],
                client_secret=creds_data['client_secret'],
                scopes=creds_data['scopes'],
                expiry=expiry
            )

            # Refresh if necessary
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                self._save_credentials(user_id, credentials)

            return credentials

        except Exception as e:
            print(f"Error retrieving credentials: {str(e)}")
            return None

    def _save_credentials(self, user_id, credentials):
        """
        Args:
            user_id (str): User identifier
            credentials (Credentials): Credentials object to save
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