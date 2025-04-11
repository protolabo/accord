import re
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, EmailStr
from fastapi import HTTPException

class StandardizedAttachment(BaseModel):
    filename: str
    content_type: str
    size: int
    content_id: Optional[str] = None
    url: Optional[str] = None

class StandardizedEmail(BaseModel):
    id: str
    external_id: str
    platform: str  # 'gmail' or 'outlook'
    subject: str
    from_name: str
    from_email: EmailStr
    to: List[str]
    cc: List[str] = []
    bcc: List[str] = []
    body: str
    body_type: str  # 'html' or 'text'
    date: datetime
    is_read: bool = False
    is_important: bool = False
    thread_id: Optional[str] = None
    categories: List[str] = []
    labels: List[str] = []
    attachments: List[StandardizedAttachment] = []

class EmailService:
    """
    Service d'abstraction pour standardiser les interactions avec les emails
    entre différentes plateformes (Gmail et Outlook)
    """
    
    @staticmethod
    def extract_email_from_address(address: str) -> str:
        """Extrait l'adresse email d'une chaîne au format 'Nom <email@example.com>'"""
        if not address:
            return ""
        
        # Si l'adresse contient des chevrons, c'est probablement un format "Nom <email>"
        if '<' in address and '>' in address:
            try:
                return re.search(r'<([^>]+)>', address).group(1)
            except:
                pass
        
        # Sinon, renvoyer l'adresse telle quelle (en supposant que c'est juste un email)
        return address
    
    @staticmethod
    def extract_name_from_address(address: str) -> str:
        """Extrait le nom d'une chaîne au format 'Nom <email@example.com>'"""
        if not address:
            return ""
            
        # Si l'adresse contient des chevrons
        if '<' in address and '>' in address:
            try:
                name = address.split('<')[0].strip()
                if name:
                    return name
            except:
                pass
            
        # Si on n'a pas pu extraire un nom, on renvoie l'adresse email
        email = EmailService.extract_email_from_address(address)
        # Utiliser la partie locale de l'email comme nom
        if '@' in email:
            return email.split('@')[0]
        return email
    
    @staticmethod
    def normalize_recipients(recipients: Union[str, List[str]]) -> List[str]:
        """Normalise une liste de destinataires en liste standard"""
        if not recipients:
            return []
            
        if isinstance(recipients, str):
            # Séparer plusieurs adresses email par virgule ou point-virgule
            if ',' in recipients:
                recipients = recipients.split(',')
            elif ';' in recipients:
                recipients = recipients.split(';')
            else:
                recipients = [recipients]
        
        return [addr.strip() for addr in recipients if addr.strip()]
    
    @staticmethod
    def convert_importance(importance: Any) -> bool:
        """Convertit divers formats d'importance en booléen standard"""
        if isinstance(importance, bool):
            return importance
        
        if isinstance(importance, str):
            importance = importance.lower()
            return importance in ('high', 'important', 'true', '1')
        
        return bool(importance)
    
    @staticmethod
    def standardize_outlook_email(outlook_email: Dict[str, Any]) -> StandardizedEmail:
        """Convertit un email Outlook en format standardisé"""
        # Extraction des informations basiques
        email_id = outlook_email.get('id', '')
        
        # Extraction des destinataires
        to_recipients = []
        if 'toRecipients' in outlook_email:
            for recipient in outlook_email['toRecipients']:
                if 'emailAddress' in recipient and 'address' in recipient['emailAddress']:
                    to_recipients.append(recipient['emailAddress']['address'])
        
        cc_recipients = []
        if 'ccRecipients' in outlook_email:
            for recipient in outlook_email['ccRecipients']:
                if 'emailAddress' in recipient and 'address' in recipient['emailAddress']:
                    cc_recipients.append(recipient['emailAddress']['address'])
        
        # Extraction de l'expéditeur
        from_email = ""
        from_name = ""
        if 'from' in outlook_email and 'emailAddress' in outlook_email['from']:
            from_email = outlook_email['from']['emailAddress'].get('address', '')
            from_name = outlook_email['from']['emailAddress'].get('name', from_email)
        
        # Extraction du corps
        body = ""
        body_type = "text"
        if 'body' in outlook_email:
            body = outlook_email['body'].get('content', '')
            body_type = outlook_email['body'].get('contentType', 'text').lower()
            if body_type not in ('html', 'text'):
                body_type = 'text'
        
        # Extraction des pièces jointes
        attachments = []
        if 'attachments' in outlook_email and outlook_email['attachments']:
            for attachment in outlook_email['attachments']:
                attachments.append(StandardizedAttachment(
                    filename=attachment.get('name', 'unnamed'),
                    content_type=attachment.get('contentType', 'application/octet-stream'),
                    size=attachment.get('size', 0),
                    content_id=attachment.get('contentId'),
                    url=attachment.get('@microsoft.graph.downloadUrl')
                ))
        
        # Format de date
        received_date = datetime.now()
        if 'receivedDateTime' in outlook_email:
            try:
                received_date = datetime.fromisoformat(outlook_email['receivedDateTime'].replace('Z', '+00:00'))
            except:
                pass
        
        # Importance
        is_important = False
        if 'importance' in outlook_email:
            is_important = outlook_email['importance'] == 'high'
        
        # Catégories
        categories = outlook_email.get('categories', [])
        
        return StandardizedEmail(
            id=str(email_id),
            external_id=email_id,
            platform='outlook',
            subject=outlook_email.get('subject', ''),
            from_name=from_name,
            from_email=from_email,
            to=to_recipients,
            cc=cc_recipients,
            body=body,
            body_type=body_type,
            date=received_date,
            is_read=outlook_email.get('isRead', False),
            is_important=is_important,
            thread_id=outlook_email.get('conversationId'),
            categories=categories,
            labels=[],
            attachments=attachments
        )
    
    @staticmethod
    def standardize_gmail_email(gmail_email: Dict[str, Any]) -> StandardizedEmail:
        """Convertit un email Gmail en format standardisé"""
        email_id = gmail_email.get('id', '')
        
        # Extraction des headers pertinents
        headers = gmail_email.get('payload', {}).get('headers', [])
        headers_dict = {h['name'].lower(): h['value'] for h in headers if 'name' in h and 'value' in h}
        
        subject = headers_dict.get('subject', '')
        from_addr = headers_dict.get('from', '')
        to_addr = headers_dict.get('to', '')
        cc_addr = headers_dict.get('cc', '')
        date_str = headers_dict.get('date', '')
        
        # Extraction de l'expéditeur
        from_email = EmailService.extract_email_from_address(from_addr)
        from_name = EmailService.extract_name_from_address(from_addr)
        
        # Normalisation des destinataires
        to_recipients = EmailService.normalize_recipients(to_addr)
        cc_recipients = EmailService.normalize_recipients(cc_addr)
        
        # Format de date
        received_date = datetime.now()
        if date_str:
            try:
                # Les dates d'email peuvent être dans divers formats, on essaie de les analyser
                from email.utils import parsedate_to_datetime
                received_date = parsedate_to_datetime(date_str)
            except:
                pass
        
        # Extraction du corps et des pièces jointes
        body = ""
        body_type = "text"
        attachments = []
        
        # Fonction récursive pour traiter les parties MIME
        def process_part(part):
            nonlocal body, body_type
            
            mime_type = part.get('mimeType', '')
            
            # Traiter le corps du message
            if mime_type == 'text/html' and (not body or body_type != 'html'):
                body_data = part.get('body', {}).get('data', '')
                if body_data:
                    import base64
                    body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                    body_type = 'html'
            elif mime_type == 'text/plain' and not body:
                body_data = part.get('body', {}).get('data', '')
                if body_data:
                    import base64
                    body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                    body_type = 'text'
            
            # Traiter les pièces jointes
            filename = part.get('filename', '')
            if filename and 'body' in part:
                attachment_id = part['body'].get('attachmentId')
                if attachment_id:
                    attachments.append(StandardizedAttachment(
                        filename=filename,
                        content_type=mime_type,
                        size=int(part['body'].get('size', 0)),
                        content_id=next((h['value'] for h in part.get('headers', []) 
                                       if h.get('name', '').lower() == 'content-id'), None),
                        url=f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{email_id}/attachments/{attachment_id}"
                    ))
            
            # Traiter récursivement les sous-parties
            if 'parts' in part:
                for sub_part in part['parts']:
                    process_part(sub_part)
        
        # Traiter la charge utile
        if 'payload' in gmail_email:
            process_part(gmail_email['payload'])
        
        # Extraction des étiquettes
        labels = gmail_email.get('labelIds', [])
        
        # Déterminer l'importance
        is_important = 'IMPORTANT' in labels
        
        # Mapper les étiquettes Gmail en catégories standardisées
        categories = []
        label_category_map = {
            'CATEGORY_PERSONAL': 'personal',
            'CATEGORY_SOCIAL': 'social',
            'CATEGORY_PROMOTIONS': 'promotions',
            'CATEGORY_UPDATES': 'updates',
            'CATEGORY_FORUMS': 'forums'
        }
        
        for label in labels:
            if label in label_category_map:
                categories.append(label_category_map[label])
        
        return StandardizedEmail(
            id=str(email_id),
            external_id=email_id,
            platform='gmail',
            subject=subject,
            from_name=from_name,
            from_email=from_email,
            to=to_recipients,
            cc=cc_recipients,
            body=body,
            body_type=body_type,
            date=received_date,
            is_read=not ('UNREAD' in labels),
            is_important=is_important,
            thread_id=gmail_email.get('threadId'),
            categories=categories,
            labels=labels,
            attachments=attachments
        )