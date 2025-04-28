from typing import List, Dict, Optional, Any
from fastapi import APIRouter, Depends, Query, HTTPException, Body
from app.services.email.email_provider import EmailProvider, get_email_provider
from app.services.email.email_service import StandardizedEmail
from app.core.security import get_current_user
from app.db.models import User
from pydantic import BaseModel, EmailStr
from datetime import datetime
import os
import json
from backend.app.utils.absolute_path import get_file_path

router = APIRouter()

class EmailResponse(BaseModel):
    emails: List[Dict[str, Any]]
    total: int
    count: int

class EmailRequest(BaseModel):
    to: List[str]
    cc: List[str] = []
    bcc: List[str] = []
    subject: str
    body: str
    body_type: str = "text"  # "text" ou "html"

# Fonction pour obtenir le fournisseur d'email comme une dépendance FastAPI
async def get_provider(user: User = Depends(get_current_user)) -> EmailProvider:
    """
    Dependency pour obtenir un fournisseur d'email pour l'utilisateur authentifié.
    """
    return EmailProvider(user)

@router.get("/emails")
async def get_emails(
    platform: Optional[str] = Query(None, description="Plateforme à utiliser (gmail, outlook ou aucune pour les deux)"),
    limit: int = Query(50, description="Nombre maximum d'emails à récupérer"),
    skip: int = Query(0, description="Nombre d'emails à sauter (pagination)"),
    folder: Optional[str] = Query(None, description="ID du dossier ou label"),
    query: Optional[str] = Query(None, description="Termes de recherche"),
    email_provider: EmailProvider = Depends(get_provider)
) -> EmailResponse:
    """
    Récupère les emails de l'utilisateur avec pagination et filtrage optionnel.
    Si aucune plateforme n'est spécifiée, récupère des deux sources (Gmail et Outlook).
    """
    if platform and platform not in ["gmail", "outlook"]:
        raise HTTPException(status_code=400, detail="La plateforme doit être 'gmail', 'outlook' ou non spécifiée")
    
    try:
        # Récupérer les emails
        emails = await email_provider.get_emails(
            platform=platform,
            limit=limit,
            skip=skip,
            folder=folder,
            query=query
        )
        
        # Convertir les emails en dictionnaires pour la réponse JSON
        email_dicts = [email.dict() for email in emails]
        
        return EmailResponse(
            emails=email_dicts,
            total=len(email_dicts),  # Dans l'idéal, il faudrait avoir un count total sans pagination
            count=len(email_dicts)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/emails/{email_id}")
async def get_email(
    email_id: str,
    platform: str = Query(..., description="Plateforme de l'email (gmail ou outlook)"),
    email_provider: EmailProvider = Depends(get_provider)
) -> Dict[str, Any]:
    """
    Récupère un email spécifique par son ID.
    """
    if platform not in ["gmail", "outlook"]:
        raise HTTPException(status_code=400, detail="La plateforme doit être 'gmail' ou 'outlook'")
    
    try:
        email = await email_provider.get_email_by_id(email_id, platform)
        return email.dict()
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Email non trouvé: {str(e)}")

@router.post("/emails")
async def send_email(
    platform: str = Query(..., description="Plateforme à utiliser pour l'envoi (gmail ou outlook)"),
    email_data: EmailRequest = Body(...),
    email_provider: EmailProvider = Depends(get_provider)
) -> Dict[str, Any]:
    """
    Envoie un nouvel email.
    """
    if platform not in ["gmail", "outlook"]:
        raise HTTPException(status_code=400, detail="La plateforme doit être 'gmail' ou 'outlook'")
    
    try:
        result = await email_provider.send_email(platform, email_data.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'envoi de l'email: {str(e)}")

@router.patch("/emails/{email_id}/read")
async def mark_as_read(
    email_id: str,
    platform: str = Query(..., description="Plateforme de l'email (gmail ou outlook)"),
    read: bool = Query(True, description="True pour marquer comme lu, False pour non lu"),
    email_provider: EmailProvider = Depends(get_provider)
) -> Dict[str, Any]:
    """
    Marque un email comme lu ou non lu.
    """
    if platform not in ["gmail", "outlook"]:
        raise HTTPException(status_code=400, detail="La plateforme doit être 'gmail' ou 'outlook'")
    
    try:
        result = await email_provider.mark_as_read(email_id, platform, read)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du marquage de l'email: {str(e)}")

@router.get("/folders")
async def get_folders(
    platform: Optional[str] = Query(None, description="Plateforme à utiliser (gmail, outlook ou aucune pour les deux)"),
    email_provider: EmailProvider = Depends(get_provider)
) -> Dict[str, Any]:
    """
    Récupère les dossiers/labels disponibles pour l'utilisateur.
    """
    if platform and platform not in ["gmail", "outlook"]:
        raise HTTPException(status_code=400, detail="La plateforme doit être 'gmail', 'outlook' ou non spécifiée")
    
    try:
        folders = await email_provider.get_folders(platform)
        return {"folders": folders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des dossiers: {str(e)}")

@router.get("/profile")
async def get_email_profile(
    platform: str = Query(..., description="Plateforme à utiliser (gmail ou outlook)"),
    email_provider: EmailProvider = Depends(get_provider)
) -> Dict[str, Any]:
    """
    Récupère le profil de l'utilisateur pour la plateforme d'email spécifiée.
    """
    if platform not in ["gmail", "outlook"]:
        raise HTTPException(status_code=400, detail="La plateforme doit être 'gmail' ou 'outlook'")
    
    try:
        # À implémenter: récupérer le profil utilisateur
        return {
            "email": email_provider.user.email,
            "platform": platform,
            "authenticated": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération du profil: {str(e)}")

@router.get("/classified-emails")
async def get_classified_emails(
    batch_number: Optional[int] = Query(None),
    output_dir: Optional[str] = Query(None)
):
    """
    Récupère les emails classifiés depuis les fichiers JSON.
    
    Args:
        batch_number: Numéro du lot à récupérer (si None, retourne tous les emails)
        output_dir: Répertoire contenant les fichiers batch (si None, utilise le répertoire par défaut)
    """
    try:
        # Utiliser le répertoire par défaut si aucun n'est spécifié
        if not output_dir:
            output_dir = get_file_path("backend/app/data/mockdata")
        
        # Vérifier si le répertoire existe
        if not os.path.exists(output_dir):
            raise HTTPException(status_code=404, detail=f"Répertoire {output_dir} non trouvé")
            
        # Déterminer les fichiers à lire
        if batch_number is not None:
            # Lire un lot spécifique
            batch_file = f"emails_batch_{batch_number}.json"
            
            # Pour le mode test (avec emails.json)
            if not os.path.exists(os.path.join(output_dir, batch_file)) and os.path.exists(os.path.join(output_dir, "emails.json")):
                batch_file = "emails.json"
                
            file_path = os.path.join(output_dir, batch_file)
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail=f"Fichier {batch_file} non trouvé")
                
            with open(file_path, 'r', encoding='utf-8') as f:
                emails = json.load(f)
            
            return {
                "total_emails": len(emails),
                "batch": batch_number,
                "emails": emails
            }
        else:
            # Lire tous les lots
            all_emails = []
            
            # Vérifier si nous sommes en mode test (avec un seul fichier emails.json)
            if os.path.exists(os.path.join(output_dir, "emails.json")):
                with open(os.path.join(output_dir, "emails.json"), 'r', encoding='utf-8') as f:
                    all_emails = json.load(f)
                    
                return {
                    "total_emails": len(all_emails),
                    "mode": "test",
                    "emails": all_emails
                }
            
            # Sinon, lire tous les fichiers batch
            batch_files = [f for f in os.listdir(output_dir) if f.startswith("emails_batch_") and f.endswith(".json")]
            batch_files.sort()  # Trier pour traiter les lots dans l'ordre
            
            for batch_file in batch_files:
                file_path = os.path.join(output_dir, batch_file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    batch_emails = json.load(f)
                    all_emails.extend(batch_emails)
            
            return {
                "total_emails": len(all_emails),
                "total_batches": len(batch_files),
                "mode": "production",
                "emails": all_emails
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des emails classifiés: {str(e)}")

@router.get("/classified-emails/status")
async def get_classification_status(
    output_dir: Optional[str] = Query(None)
):
    """
    Vérifie si le processus de classification est terminé en vérifiant l'existence des fichiers.
    """
    try:
        # Utiliser le répertoire par défaut si aucun n'est spécifié
        if not output_dir:
            output_dir = get_file_path("backend/app/data/mockdata")
            
        # Vérifier si le répertoire existe
        if not os.path.exists(output_dir):
            return {"status": "not_started", "message": "Le répertoire des emails n'existe pas"}
            
        # Vérifier s'il y a des fichiers d'emails
        # Mode test
        if os.path.exists(os.path.join(output_dir, "emails.json")):
            with open(os.path.join(output_dir, "emails.json"), 'r', encoding='utf-8') as f:
                emails = json.load(f)
                
            # Vérifier si au moins un email a été classifié
            if emails and "accord_main_class" in emails[0]:
                return {
                    "status": "completed", 
                    "mode": "test",
                    "total_emails": len(emails)
                }
            else:
                return {"status": "in_progress", "message": "Classification en cours"}
                
        # Mode production
        batch_files = [f for f in os.listdir(output_dir) if f.startswith("emails_batch_") and f.endswith(".json")]
        if not batch_files:
            return {"status": "not_started", "message": "Aucun fichier d'emails trouvé"}
            
        # Vérifier le premier lot pour voir s'il contient des classifications
        with open(os.path.join(output_dir, batch_files[0]), 'r', encoding='utf-8') as f:
            batch_emails = json.load(f)
            
        if batch_emails and "accord_main_class" in batch_emails[0]:
            return {
                "status": "completed", 
                "mode": "production",
                "total_batches": len(batch_files),
                "total_emails": sum(1 for f in batch_files for e in json.load(open(os.path.join(output_dir, f), 'r', encoding='utf-8')))
            }
        else:
            return {"status": "in_progress", "message": "Classification en cours"}
            
    except Exception as e:
        return {"status": "error", "message": f"Erreur lors de la vérification du statut: {str(e)}"}

