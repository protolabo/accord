from typing import List, Dict, Optional, Any, Union
from datetime import datetime, timedelta
import json
import base64
from fastapi import HTTPException, Depends
from httpx import AsyncClient, HTTPStatusError
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from app.db.models import User
from app.core.config import settings
from app.email_providers.google.gmail_auth import GmailAuthManager
from app.services.email.outlookAuth import OutlookAuth
from app.services.email.email_service import StandardizedEmail, EmailService
from app.routes.auth import get_current_user

class EmailProvider:
    """
    Service de fournisseur d'email qui permet d'interagir avec Gmail et Outlook
    en utilisant un format standardisé.
    """
    
    def __init__(self, user: User):
        """
        Initialise le fournisseur d'email pour un utilisateur donné.
        
        Args:
            user (User): L'utilisateur pour lequel le service est initialisé
        """
        self.user = user
        self._gmail_service = None
        self._outlook_client = None
    
    async def get_gmail_service(self):
        """
        Obtient le service Gmail pour l'utilisateur actuel.
        Rafraîchit les tokens si nécessaire.
        
        Returns:
            Service Gmail configuré avec les tokens de l'utilisateur
        """
        if not self.user.gmail_tokens:
            raise HTTPException(status_code=401, detail="User not authenticated with Gmail")
        
        # Vérifier si le token est expiré et le rafraîchir si nécessaire
        if self.user.is_gmail_token_expired:
            auth_manager = GmailAuthManager()
            new_tokens = auth_manager.refresh_access_token(
                self.user.gmail_tokens.get("refresh_token")
            )
            
            # Mettre à jour les tokens dans la BD
            self.user.gmail_tokens = {
                "access_token": new_tokens["access_token"],
                "refresh_token": self.user.gmail_tokens.get("refresh_token"),
                "expires_at": datetime.now() + datetime.timedelta(seconds=new_tokens["expires_in"])
            }
            await self.user.save()
        
        # Configurer les credentials Gmail
        credentials = Credentials(
            token=self.user.gmail_tokens.get("access_token"),
            refresh_token=self.user.gmail_tokens.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GMAIL_CLIENT_ID,
            client_secret=settings.GMAIL_CLIENT_SECRET,
            scopes=["https://www.googleapis.com/auth/gmail.readonly",
                   "https://www.googleapis.com/auth/gmail.send",
                   "https://www.googleapis.com/auth/gmail.modify"]
        )
        
        # Construire le service Gmail
        return build('gmail', 'v1', credentials=credentials)
    
    async def get_outlook_client(self):
        """
        Obtient un client HTTP configuré pour les appels API Microsoft Graph.
        Rafraîchit les tokens si nécessaire.
        
        Returns:
            Client HTTP configuré avec les tokens de l'utilisateur
        """
        if not self.user.outlook_tokens:
            raise HTTPException(status_code=401, detail="User not authenticated with Outlook")
        
        # Vérifier si le token est expiré et le rafraîchir si nécessaire
        if self.user.is_outlook_token_expired:
            async with AsyncClient() as client:
                try:
                    refresh_response = await client.post(
                        f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/oauth2/v2.0/token",
                        data={
                            "client_id": settings.MICROSOFT_CLIENT_ID,
                            "client_secret": settings.MICROSOFT_CLIENT_SECRET,
                            "refresh_token": self.user.outlook_tokens.get("refresh_token"),
                            "grant_type": "refresh_token",
                            "scope": "openid profile email Mail.Read Mail.ReadWrite Mail.Send"
                        }
                    )
                    refresh_response.raise_for_status()
                    tokens = refresh_response.json()
                    
                    # Mettre à jour les tokens dans la BD
                    self.user.outlook_tokens = {
                        "access_token": tokens["access_token"],
                        "refresh_token": tokens.get("refresh_token", self.user.outlook_tokens.get("refresh_token")),
                        "expires_at": datetime.now() + datetime.timedelta(seconds=tokens["expires_in"])
                    }
                    await self.user.save()
                
                except HTTPStatusError as e:
                    raise HTTPException(
                        status_code=401,
                        detail=f"Failed to refresh outlook token: {e.response.text}"
                    )
        
        # Configurer le client HTTP pour les appels à Microsoft Graph
        client = AsyncClient(headers={
            "Authorization": f"Bearer {self.user.outlook_tokens.get('access_token')}",
            "Content-Type": "application/json"
        })
        
        return client
    
    async def get_emails(self, platform: str = None, limit: int = 50, skip: int = 0, 
                        folder: str = None, query: str = None) -> List[StandardizedEmail]:
        """
        Récupère les emails de l'utilisateur depuis la plateforme spécifiée ou toutes les plateformes.
        
        Args:
            platform (str, optional): 'gmail' ou 'outlook'. Si None, essaie les deux plateformes.
            limit (int): Nombre maximal d'emails à récupérer.
            skip (int): Nombre d'emails à sauter.
            folder (str, optional): Dossier/label duquel récupérer les emails.
            query (str, optional): Requête de recherche.
            
        Returns:
            List[StandardizedEmail]: Liste d'emails au format standardisé.
        """
        all_emails = []
        
        # Déterminer quelles plateformes utiliser
        platforms_to_use = []
        if platform == 'gmail' and self.user.gmail_tokens:
            platforms_to_use.append('gmail')
        elif platform == 'outlook' and self.user.outlook_tokens:
            platforms_to_use.append('outlook')
        elif not platform:
            if self.user.gmail_tokens:
                platforms_to_use.append('gmail')
            if self.user.outlook_tokens:
                platforms_to_use.append('outlook')
        
        # Récupérer les emails de chaque plateforme
        for platform in platforms_to_use:
            try:
                if platform == 'gmail':
                    gmail_emails = await self._get_gmail_emails(limit, skip, folder, query)
                    all_emails.extend(gmail_emails)
                elif platform == 'outlook':
                    outlook_emails = await self._get_outlook_emails(limit, skip, folder, query)
                    all_emails.extend(outlook_emails)
            except Exception as e:
                # Log l'erreur mais continue avec les autres plateformes
                print(f"Error fetching emails from {platform}: {str(e)}")
        
        # Trier les emails par date, du plus récent au plus ancien
        all_emails.sort(key=lambda x: x.date, reverse=True)
        
        # Appliquer la pagination sur la liste combinée
        return all_emails[:limit]
    
    async def _get_gmail_emails(self, limit: int, skip: int, folder: str = None, 
                              query: str = None) -> List[StandardizedEmail]:
        """
        Récupère les emails depuis Gmail.
        """
        gmail_service = await self.get_gmail_service()
        
        # Construire la requête
        query_parts = []
        if query:
            query_parts.append(query)
        
        # Si un dossier est spécifié, l'ajouter à la requête
        label_filter = None
        if folder:
            label_filter = folder
        
        # Récupérer les IDs des messages
        try:
            messages_result = gmail_service.users().messages().list(
                userId='me',
                maxResults=limit + skip,
                q=' '.join(query_parts) if query_parts else None,
                labelIds=[label_filter] if label_filter else None
            ).execute()
            
            messages = messages_result.get('messages', [])
            
            # Appliquer le skip
            messages = messages[skip:skip+limit]
            
            # Récupérer les messages complets
            emails = []
            for message in messages:
                msg = gmail_service.users().messages().get(
                    userId='me', id=message['id'], format='full'
                ).execute()
                
                # Standardiser l'email
                standardized_email = EmailService.standardize_gmail_email(msg)
                emails.append(standardized_email)
            
            return emails
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching Gmail emails: {str(e)}")
    
    async def _get_outlook_emails(self, limit: int, skip: int, folder: str = None, 
                                query: str = None) -> List[StandardizedEmail]:
        """
        Récupère les emails depuis Outlook.
        """
        outlook_client = await self.get_outlook_client()
        
        # Construire l'URL de requête
        endpoint = "/me/messages"
        if folder:
            endpoint = f"/me/mailFolders/{folder}/messages"
        
        params = {
            "$top": limit,
            "$skip": skip,
            "$orderby": "receivedDateTime desc",
            "$expand": "attachments"
        }
        
        # Ajouter une requête de recherche si spécifiée
        if query:
            params["$search"] = f'"{query}"'
        
        try:
            response = await outlook_client.get(
                f"https://graph.microsoft.com/v1.0{endpoint}",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            messages = data.get('value', [])
            
            # Standardiser les emails
            emails = []
            for message in messages:
                standardized_email = EmailService.standardize_outlook_email(message)
                emails.append(standardized_email)
            
            return emails
            
        except HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error fetching Outlook emails: {e.response.text}"
            )
    
    async def get_email_by_id(self, email_id: str, platform: str) -> StandardizedEmail:
        """
        Récupère un email spécifique par son ID.
        
        Args:
            email_id (str): ID de l'email à récupérer.
            platform (str): 'gmail' ou 'outlook'.
            
        Returns:
            StandardizedEmail: L'email au format standardisé.
        """
        if platform == 'gmail' and self.user.gmail_tokens:
            return await self._get_gmail_email_by_id(email_id)
        elif platform == 'outlook' and self.user.outlook_tokens:
            return await self._get_outlook_email_by_id(email_id)
        else:
            raise HTTPException(status_code=400, detail=f"Invalid platform or user not authenticated with {platform}")
    
    async def _get_gmail_email_by_id(self, email_id: str) -> StandardizedEmail:
        """
        Récupère un email spécifique depuis Gmail.
        """
        gmail_service = await self.get_gmail_service()
        
        try:
            msg = gmail_service.users().messages().get(
                userId='me', id=email_id, format='full'
            ).execute()
            
            # Standardiser l'email
            return EmailService.standardize_gmail_email(msg)
            
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Gmail email not found: {str(e)}")
    
    async def _get_outlook_email_by_id(self, email_id: str) -> StandardizedEmail:
        """
        Récupère un email spécifique depuis Outlook.
        """
        outlook_client = await self.get_outlook_client()
        
        try:
            response = await outlook_client.get(
                f"https://graph.microsoft.com/v1.0/me/messages/{email_id}?$expand=attachments"
            )
            response.raise_for_status()
            
            message = response.json()
            
            # Standardiser l'email
            return EmailService.standardize_outlook_email(message)
            
        except HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code or 404,
                detail=f"Outlook email not found: {e.response.text}"
            )
    
    async def send_email(self, platform: str, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envoie un email via la plateforme spécifiée.
        
        Args:
            platform (str): 'gmail' ou 'outlook'.
            email_data (Dict): Données de l'email à envoyer.
            
        Returns:
            Dict: Résultat de l'envoi.
        """
        if platform == 'gmail' and self.user.gmail_tokens:
            return await self._send_gmail_email(email_data)
        elif platform == 'outlook' and self.user.outlook_tokens:
            return await self._send_outlook_email(email_data)
        else:
            raise HTTPException(status_code=400, detail=f"Invalid platform or user not authenticated with {platform}")
    
    async def _send_gmail_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envoie un email via Gmail.
        """
        gmail_service = await self.get_gmail_service()
        
        try:
            # Construire le corps du message
            message = {
                'raw': self._create_gmail_raw_message(email_data)
            }
            
            # Envoyer le message
            sent_message = gmail_service.users().messages().send(
                userId='me', body=message
            ).execute()
            
            return {
                'success': True,
                'message_id': sent_message.get('id', ''),
                'platform': 'gmail'
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error sending Gmail email: {str(e)}")
    
    def _create_gmail_raw_message(self, email_data: Dict[str, Any]) -> str:
        """
        Crée un message Gmail brut à partir des données d'email.
        """
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        import base64
        
        # Créer le message
        message = MIMEMultipart()
        message['to'] = ', '.join(email_data.get('to', []))
        if email_data.get('cc'):
            message['cc'] = ', '.join(email_data.get('cc', []))
        if email_data.get('bcc'):
            message['bcc'] = ', '.join(email_data.get('bcc', []))
        message['subject'] = email_data.get('subject', '')
        
        # Ajouter le corps du message
        body_type = email_data.get('body_type', 'text')
        if body_type == 'html':
            message.attach(MIMEText(email_data.get('body', ''), 'html'))
        else:
            message.attach(MIMEText(email_data.get('body', ''), 'plain'))
        
        # Encoder le message en base64
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        return raw_message
    
    async def _send_outlook_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envoie un email via Outlook.
        """
        outlook_client = await self.get_outlook_client()
        
        # Construire le corps de la requête
        message = {
            'message': {
                'subject': email_data.get('subject', ''),
                'body': {
                    'contentType': 'HTML' if email_data.get('body_type') == 'html' else 'Text',
                    'content': email_data.get('body', '')
                },
                'toRecipients': [{'emailAddress': {'address': email}} for email in email_data.get('to', [])],
            },
            'saveToSentItems': 'true'
        }
        
        # Ajouter les destinataires en copie si présents
        if email_data.get('cc'):
            message['message']['ccRecipients'] = [
                {'emailAddress': {'address': email}} for email in email_data.get('cc', [])
            ]
        
        # Ajouter les destinataires en copie cachée si présents
        if email_data.get('bcc'):
            message['message']['bccRecipients'] = [
                {'emailAddress': {'address': email}} for email in email_data.get('bcc', [])
            ]
        
        try:
            response = await outlook_client.post(
                "https://graph.microsoft.com/v1.0/me/sendMail",
                json=message
            )
            response.raise_for_status()
            
            # Outlook ne renvoie pas d'ID pour les messages envoyés via cette API
            # On renvoie simplement un succès
            return {
                'success': True,
                'platform': 'outlook'
            }
            
        except HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error sending Outlook email: {e.response.text}"
            )
    
    async def mark_as_read(self, email_id: str, platform: str, read: bool = True) -> Dict[str, Any]:
        """
        Marque un email comme lu ou non lu.
        
        Args:
            email_id (str): ID de l'email à modifier.
            platform (str): 'gmail' ou 'outlook'.
            read (bool): True pour marquer comme lu, False pour marquer comme non lu.
            
        Returns:
            Dict: Résultat de l'opération.
        """
        if platform == 'gmail' and self.user.gmail_tokens:
            return await self._mark_gmail_as_read(email_id, read)
        elif platform == 'outlook' and self.user.outlook_tokens:
            return await self._mark_outlook_as_read(email_id, read)
        else:
            raise HTTPException(status_code=400, detail=f"Invalid platform or user not authenticated with {platform}")
    
    async def _mark_gmail_as_read(self, email_id: str, read: bool = True) -> Dict[str, Any]:
        """
        Marque un email Gmail comme lu ou non lu.
        """
        gmail_service = await self.get_gmail_service()
        
        try:
            # Déterminer les modifications à apporter
            if read:
                # Supprimer le label UNREAD
                body = {'removeLabelIds': ['UNREAD']}
            else:
                # Ajouter le label UNREAD
                body = {'addLabelIds': ['UNREAD']}
            
            # Modifier le message
            gmail_service.users().messages().modify(
                userId='me', id=email_id, body=body
            ).execute()
            
            return {
                'success': True,
                'message_id': email_id,
                'platform': 'gmail',
                'is_read': read
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error marking Gmail email: {str(e)}")
    
    async def _mark_outlook_as_read(self, email_id: str, read: bool = True) -> Dict[str, Any]:
        """
        Marque un email Outlook comme lu ou non lu.
        """
        outlook_client = await self.get_outlook_client()
        
        try:
            response = await outlook_client.patch(
                f"https://graph.microsoft.com/v1.0/me/messages/{email_id}",
                json={'isRead': read}
            )
            response.raise_for_status()
            
            return {
                'success': True,
                'message_id': email_id,
                'platform': 'outlook',
                'is_read': read
            }
            
        except HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error marking Outlook email: {e.response.text}"
            )
    
    async def get_folders(self, platform: str = None) -> List[Dict[str, Any]]:
        """
        Récupère les dossiers/labels de l'utilisateur.
        
        Args:
            platform (str, optional): 'gmail' ou 'outlook'. Si None, essaie les deux plateformes.
            
        Returns:
            List[Dict]: Liste des dossiers disponibles.
        """
        all_folders = []
        
        # Déterminer quelles plateformes utiliser
        platforms_to_use = []
        if platform == 'gmail' and self.user.gmail_tokens:
            platforms_to_use.append('gmail')
        elif platform == 'outlook' and self.user.outlook_tokens:
            platforms_to_use.append('outlook')
        elif not platform:
            if self.user.gmail_tokens:
                platforms_to_use.append('gmail')
            if self.user.outlook_tokens:
                platforms_to_use.append('outlook')
        
        # Récupérer les dossiers de chaque plateforme
        for platform in platforms_to_use:
            try:
                if platform == 'gmail':
                    gmail_folders = await self._get_gmail_folders()
                    all_folders.extend(gmail_folders)
                elif platform == 'outlook':
                    outlook_folders = await self._get_outlook_folders()
                    all_folders.extend(outlook_folders)
            except Exception as e:
                # Log l'erreur mais continue avec les autres plateformes
                print(f"Error fetching folders from {platform}: {str(e)}")
        
        return all_folders
    
    async def _get_gmail_folders(self) -> List[Dict[str, Any]]:
        """
        Récupère les labels Gmail.
        """
        gmail_service = await self.get_gmail_service()
        
        try:
            # Récupérer les labels
            labels_result = gmail_service.users().labels().list(userId='me').execute()
            labels = labels_result.get('labels', [])
            
            # Standardiser les labels
            folders = []
            for label in labels:
                folders.append({
                    'id': label['id'],
                    'name': label['name'],
                    'platform': 'gmail',
                    'type': 'system' if label['type'] == 'system' else 'user'
                })
            
            return folders
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching Gmail labels: {str(e)}")
    
    async def _get_outlook_folders(self) -> List[Dict[str, Any]]:
        """
        Récupère les dossiers Outlook.
        """
        outlook_client = await self.get_outlook_client()
        
        try:
            response = await outlook_client.get(
                "https://graph.microsoft.com/v1.0/me/mailFolders?$top=100"
            )
            response.raise_for_status()
            
            data = response.json()
            folders = data.get('value', [])
            
            # Standardiser les dossiers
            standardized_folders = []
            for folder in folders:
                standardized_folders.append({
                    'id': folder['id'],
                    'name': folder['displayName'],
                    'platform': 'outlook',
                    'type': 'system' if folder.get('wellKnownName') else 'user',
                    'unread_count': folder.get('unreadItemCount', 0),
                    'total_count': folder.get('totalItemCount', 0)
                })
            
            return standardized_folders
            
        except HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error fetching Outlook folders: {e.response.text}"
            )

# Fonction pour obtenir le fournisseur d'email comme une dépendance FastAPI
async def get_email_provider(user: User = Depends(get_current_user)) -> EmailProvider:
    """
    Dependency pour obtenir un fournisseur d'email pour l'utilisateur authentifié.
    """
    return EmailProvider(user)