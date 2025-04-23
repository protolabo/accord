import base64
import time
from email.header import decode_header
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime

from backend.app.email_providers.google.gmail_auth import GmailAuthManager



class GmailService:
    """Service amélioré pour interagir avec l'API Gmail."""

    def __init__(self, credentials_path=None, tokens_dir=None):
        """
        Initialise le service Gmail.

        Args:
            credentials_path: Chemin vers le fichier client_secret.json
            tokens_dir: Répertoire pour stocker les jetons d'authentification
        """
        from backend.app.email_providers.google.settings import Config
        self.auth_manager = GmailAuthManager(
            credentials_path or Config.GOOGLE_CREDENTIALS_PATH,
            tokens_dir or Config.TOKEN_DIR
        )

    def get_service(self, user_id):
        """
        Obtient une instance authentifiée du service Gmail API.

        Args:
            user_id: Identifiant de l'utilisateur

        Returns:
            Service Gmail ou None si l'authentification échoue
        """
        credentials = self.auth_manager.get_credentials(user_id)

        if not credentials:
            raise ValueError(f"Utilisateur {user_id} non authentifié")

        return build('gmail', 'v1', credentials=credentials)

    def fetch_all_emails(self, user_id, max_results=None, batch_size=100):
        """
        Récupère tous les emails de l'utilisateur.

        Args:
            user_id: Identifiant de l'utilisateur
            max_results: Nombre maximum d'emails à récupérer (None = tous)
            batch_size: Taille des lots pour les requêtes API

        Returns:
            list: Liste des emails formatés
        """
        try:
            service = self.get_service(user_id)
            return self._fetch_emails_in_batches(service, max_results, batch_size)
        except Exception as e:
            print(f"Erreur lors de la récupération des emails: {str(e)}")
            raise

    def _fetch_emails_in_batches(self, service, max_results=None, batch_size=100):
        """
        Récupère les emails par lots pour optimiser les performances.

        Args:
            service: Service Gmail API
            max_results: Nombre maximum d'emails à récupérer
            batch_size: Taille des lots

        Returns:
            list: Liste des emails formatés
        """
        emails = []
        messages_fetched = 0

        request = service.users().messages().list(userId='me', maxResults=batch_size)

        # Boucle pour la pagination
        while request is not None:
            try:
                response = request.execute()
                messages_batch = response.get('messages', [])

                if messages_batch:
                    print(f"Traitement du lot de {len(messages_batch)} emails...")

                    for i, message_data in enumerate(messages_batch):
                        if max_results and messages_fetched >= max_results:
                            break

                        try:
                            email_data = self._get_email_details(service, message_data['id'])
                            if email_data:
                                emails.append(email_data)
                                messages_fetched += 1

                            # Afficher la progression
                            if i % 10 == 0:
                                print(f"Progression: {messages_fetched} emails récupérés")

                            # Respecter les quotas
                            time.sleep(0.05)
                        except Exception as e:
                            print(f"Erreur pour l'email {message_data['id']}: {str(e)}")

                # Arrêter si max_results atteint
                if max_results and messages_fetched >= max_results:
                    break

                # Préparer la page suivante
                request = service.users().messages().list_next(
                    previous_request=request, previous_response=response)

            except HttpError as error:
                if error.resp.status in [429, 500, 503]:
                    # Pause en cas de limitation
                    wait_time = error.resp.retry_after if hasattr(error.resp, 'retry_after') else 10
                    print(f"Limitation d'API détectée. Pause de {wait_time} secondes...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise

        print(f"Récupération terminée. {len(emails)} emails récupérés.")
        return emails

    def _get_email_details(self, service, msg_id):
        """
        Récupère les détails d'un email spécifique.

        Args:
            service: Service Gmail API
            msg_id: Identifiant du message

        Returns:
            dict: Données formatées de l'email
        """
        try:
            message = service.users().messages().get(
                userId='me', id=msg_id, format='full').execute()

            email_data = {
                "Message-ID": msg_id,
                "Thread-ID": message.get('threadId', ''),
                "Labels": message.get('labelIds', []),
                "Date": "",
                "From": "",
                "To": "",
                "Cc": "",
                "Bcc": "",
                "Subject": "",
                "Body": {
                    "plain": "",
                    "html": ""
                },
                "Attachments": [],
                "Categories": [],
                "Snippet": message.get('snippet', ''),
                "Internal-Date": self._format_timestamp(message.get('internalDate'))
            }

            headers = message['payload'].get('headers', [])
            for header in headers:
                name = header['name'].lower()
                value = header['value']

                if name == 'date':
                    email_data['Date'] = value
                elif name == 'from':
                    email_data['From'] = value
                elif name == 'to':
                    email_data['To'] = value
                elif name == 'cc':
                    email_data['Cc'] = value
                elif name == 'bcc':
                    email_data['Bcc'] = value
                elif name == 'subject':
                    email_data['Subject'] = self._decode_header_text(value)

            self._process_parts(message['payload'], email_data)

            return email_data

        except Exception as e:
            print(f"Erreur lors de l'extraction des détails de l'email {msg_id}: {str(e)}")
            return None

    def _process_parts(self, payload, email_data, is_attachment=False, filename="", parent_part=None):
        """
        Traite récursivement les parties d'un email pour extraire le corps et les pièces jointes.

        Args:
            payload: Partie du message à traiter
            email_data: Dictionnaire contenant les données de l'email
            is_attachment: Indique si la partie est une pièce jointe
            filename: Nom de fichier pour les pièces jointes
            parent_part: Partie parente pour le contexte multipart
        """
        if 'parts' in payload:
            for part in payload['parts']:
                part_filename = ""
                if 'filename' in part.get('body', {}) and part['body'].get('filename'):
                    part_filename = part['body']['filename']
                elif 'headers' in part:
                    for header in part['headers']:
                        if header['name'].lower() == 'content-disposition':
                            for param in header['value'].split(';'):
                                if 'filename=' in param:
                                    part_filename = param.split('=')[1].strip('"\'')

                part_is_attachment = is_attachment or bool(part_filename)

                self._process_parts(part, email_data, part_is_attachment, part_filename, payload)
        else:
            if is_attachment and 'body' in payload and 'attachmentId' in payload['body']:
                attachment = {
                    'id': payload['body']['attachmentId'],
                    'filename': filename or "unnamed_attachment",
                    'mimeType': payload.get('mimeType', 'application/octet-stream'),
                    'size': payload['body'].get('size', 0)
                }
                email_data['Attachments'].append(attachment)
            elif 'body' in payload and 'data' in payload['body']:
                data = payload['body']['data']
                decoded_data = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')

                mime_type = payload.get('mimeType', '')
                if 'text/plain' in mime_type:
                    email_data['Body']['plain'] += decoded_data
                elif 'text/html' in mime_type:
                    email_data['Body']['html'] += decoded_data

    def _decode_header_text(self, text):
        """
        Args:
            text: Texte de l'en-tête à décoder

        Returns:
            str: Texte décodé
        """
        try:
            parts = decode_header(text)
            decoded_parts = []

            for part, encoding in parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_parts.append(part.decode(encoding, errors='replace'))
                    else:
                        decoded_parts.append(part.decode('utf-8', errors='replace'))
                else:
                    decoded_parts.append(part)

            return ''.join(decoded_parts)
        except Exception as e:
            print(f"Erreur lors du décodage de l'en-tête: {str(e)}")
            return text

    def _format_timestamp(self, timestamp_ms):
        """
        Convertit un timestamp en millisecondes en format ISO.

        Args:
            timestamp_ms: Timestamp en millisecondes

        Returns:
            str: Date au format ISO ou chaîne vide si invalide
        """
        if not timestamp_ms:
            return ""

        try:
            timestamp_sec = int(timestamp_ms) / 1000.0
            dt = datetime.fromtimestamp(timestamp_sec)
            return dt.isoformat()
        except (ValueError, TypeError) as e:
            print(f"Erreur lors de la conversion du timestamp {timestamp_ms}: {str(e)}")
            return ""