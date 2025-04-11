from typing import List, Dict, Optional, Any
from fastapi import APIRouter, Depends, Query, HTTPException, Body
from app.services.email.email_provider import EmailProvider, get_email_provider
from app.services.email.email_service import StandardizedEmail
from app.routes.auth import get_current_user
from app.db.models import User
from pydantic import BaseModel, EmailStr
from datetime import datetime

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

