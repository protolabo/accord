"""
Tâche de synchronisation des emails pour tous les utilisateurs actifs.
Cette tâche est exécutée en arrière-plan à intervalles réguliers pour
récupérer les nouveaux emails depuis Gmail et Outlook et les stocker dans MongoDB.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from app.db.models import User, Email
from app.services.email.email_provider import EmailProvider
from app.core.config import settings

logger = logging.getLogger(__name__)

async def sync_emails_for_user(user: User):
    """
    Synchronise les emails pour un utilisateur spécifique.
    Récupère les nouveaux emails de toutes les plateformes auxquelles l'utilisateur est connecté.
    """
    logger.info(f"Synchronisation des emails pour l'utilisateur {user.email}")
    
    try:
        email_provider = EmailProvider(user)
        
        # Synchroniser les emails depuis Gmail si l'utilisateur a une authentification Gmail
        if user.gmail_tokens and not user.is_gmail_token_expired:
            try:
                # Récupérer la date du dernier email synchronisé
                last_email = await Email.find(
                    (Email.user_id == str(user.id)) & (Email.platform == "gmail")
                ).sort(-Email.received_at).limit(1).to_list()
                
                since_date = None
                if last_email:
                    since_date = last_email[0].received_at - timedelta(days=1)  # Chevauchement pour éviter les trous
                
                # Construire le filtre de date
                query = None
                if since_date:
                    query = f"after:{since_date.strftime('%Y/%m/%d')}"
                
                # Récupérer les nouveaux emails
                gmail_emails = await email_provider._get_gmail_emails(
                    limit=100,  # Limiter à 100 emails par synchronisation
                    skip=0,
                    query=query
                )
                
                # Sauvegarder les emails dans MongoDB
                for std_email in gmail_emails:
                    # Vérifier si cet email existe déjà dans la base de données
                    existing_email = await Email.find_one(
                        (Email.user_id == str(user.id)) & 
                        (Email.external_id == std_email.external_id) &
                        (Email.platform == "gmail")
                    )
                    
                    if not existing_email:
                        # Créer un nouvel objet Email à partir du StandardizedEmail
                        email = Email(
                            user_id=str(user.id),
                            platform="gmail",
                            email_id=str(std_email.id),
                            external_id=std_email.external_id,
                            thread_id=std_email.thread_id,
                            sender=std_email.from_name,
                            sender_email=std_email.from_email,
                            to=std_email.to,
                            cc=std_email.cc,
                            subject=std_email.subject,
                            body=std_email.body,
                            body_type=std_email.body_type,
                            received_at=std_email.date if isinstance(std_email.date, datetime) else datetime.fromisoformat(str(std_email.date)),
                            is_read=std_email.is_read,
                            is_important=std_email.is_important,
                            categories=std_email.categories,
                            labels=std_email.labels or [],
                            has_attachments=len(std_email.attachments) > 0,
                            attachments=[{
                                "filename": att.filename,
                                "content_type": att.content_type,
                                "size": att.size,
                                "content_id": att.content_id,
                                "url": att.url
                            } for att in std_email.attachments],
                            is_processed=False
                        )
                        await email.save()
                        logger.debug(f"Email Gmail sauvegardé: {email.subject}")
                
                logger.info(f"Synchronisation Gmail terminée pour {user.email}: {len(gmail_emails)} emails récupérés")
            
            except Exception as e:
                logger.error(f"Erreur lors de la synchronisation Gmail pour {user.email}: {str(e)}")
        
        # Synchroniser les emails depuis Outlook si l'utilisateur a une authentification Outlook
        if user.outlook_tokens and not user.is_outlook_token_expired:
            try:
                # Récupérer la date du dernier email synchronisé
                last_email = await Email.find(
                    (Email.user_id == str(user.id)) & (Email.platform == "outlook")
                ).sort(-Email.received_at).limit(1).to_list()
                
                # Récupérer les nouveaux emails
                # Note: Outlook utilise un filtre différent pour la date
                outlook_emails = await email_provider._get_outlook_emails(
                    limit=100,  # Limiter à 100 emails par synchronisation
                    skip=0,
                    # Nous n'utilisons pas de filtre de date ici car l'API Outlook triera par date de réception
                )
                
                # Sauvegarder les emails dans MongoDB
                for std_email in outlook_emails:
                    # Vérifier si cet email existe déjà dans la base de données
                    existing_email = await Email.find_one(
                        (Email.user_id == str(user.id)) & 
                        (Email.external_id == std_email.external_id) &
                        (Email.platform == "outlook")
                    )
                    
                    if not existing_email:
                        # Créer un nouvel objet Email à partir du StandardizedEmail
                        email = Email(
                            user_id=str(user.id),
                            platform="outlook",
                            email_id=str(std_email.id),
                            external_id=std_email.external_id,
                            thread_id=std_email.thread_id,
                            sender=std_email.from_name,
                            sender_email=std_email.from_email,
                            to=std_email.to,
                            cc=std_email.cc,
                            subject=std_email.subject,
                            body=std_email.body,
                            body_type=std_email.body_type,
                            received_at=std_email.date if isinstance(std_email.date, datetime) else datetime.fromisoformat(str(std_email.date)),
                            is_read=std_email.is_read,
                            is_important=std_email.is_important,
                            categories=std_email.categories,
                            labels=std_email.labels or [],
                            has_attachments=len(std_email.attachments) > 0,
                            attachments=[{
                                "filename": att.filename,
                                "content_type": att.content_type,
                                "size": att.size,
                                "content_id": att.content_id,
                                "url": att.url
                            } for att in std_email.attachments],
                            is_processed=False
                        )
                        await email.save()
                        logger.debug(f"Email Outlook sauvegardé: {email.subject}")
                
                logger.info(f"Synchronisation Outlook terminée pour {user.email}: {len(outlook_emails)} emails récupérés")
            
            except Exception as e:
                logger.error(f"Erreur lors de la synchronisation Outlook pour {user.email}: {str(e)}")
    
    except Exception as e:
        logger.error(f"Erreur générale lors de la synchronisation pour {user.email}: {str(e)}")

async def sync_all_users_emails():
    """
    Synchronise les emails pour tous les utilisateurs actifs.
    Cette fonction est exécutée périodiquement pour maintenir la base de données à jour.
    """
    logger.info("Démarrage de la synchronisation des emails pour tous les utilisateurs")
    
    try:
        # Récupérer tous les utilisateurs qui ont au moins une authentification de service d'email
        users = await User.find(
            {"$or": [
                {"gmail_tokens": {"$ne": None}},
                {"outlook_tokens": {"$ne": None}}
            ]}
        ).to_list()
        
        logger.info(f"Nombre d'utilisateurs à synchroniser: {len(users)}")
        
        # Synchroniser les emails pour chaque utilisateur
        for user in users:
            await sync_emails_for_user(user)
        
        logger.info("Synchronisation terminée pour tous les utilisateurs")
    
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation globale: {str(e)}")

# Fonction pour démarrer une tâche périodique
async def start_email_sync_task():
    """
    Démarre une tâche périodique pour synchroniser les emails.
    L'intervalle est défini dans les paramètres de l'application.
    """
    while True:
        try:
            await sync_all_users_emails()
        except Exception as e:
            logger.error(f"Erreur dans la tâche de synchronisation: {str(e)}")
        
        # Attendre l'intervalle défini avant la prochaine synchronisation
        await asyncio.sleep(settings.EMAIL_SYNC_INTERVAL)