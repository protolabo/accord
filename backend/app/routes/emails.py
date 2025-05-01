import json
import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from backend.app.utils.absolute_path import get_file_path
from backend.app.email_providers.google.email_utils import normalize_email_for_storage
from backend.app.core.security import SECRET_KEY, ALGORITHM



security = HTTPBearer()
router = APIRouter(prefix="/emails")


@router.get("/status")
async def get_emails_status(
        email: str = Query(...),
        authorization: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Récupère le statut de l'exportation des emails pour un utilisateur spécifique
    """
    try:
        try:
            payload = jwt.decode(authorization.credentials, SECRET_KEY, algorithms=[ALGORITHM])
            token_email = payload.get("email")

            # Vérifier que l'email du token correspond à l'email demandé
            if token_email != email:
                raise HTTPException(status_code=403, detail="Accès non autorisé")
        except JWTError:
            raise HTTPException(status_code=401, detail="Token invalide")

        # Récupérer le chemin du répertoire pour cet utilisateur
        user_id = normalize_email_for_storage(email)
        export_dir = get_file_path(f"backend/app/data")

        # Vérifier si le répertoire existe
        if not os.path.exists(export_dir):
            return {
                "status": "not_started",
                "message": "Aucune exportation d'emails n'a été démarrée pour cet utilisateur",
                "total_emails": 0,
                "total_batches": 0
            }

        # Vérifier s'il existe un fichier d'index
        index_file = os.path.join(export_dir, "index.json")
        if os.path.exists(index_file):
            with open(index_file, "r", encoding="utf-8") as f:
                index_data = json.load(f)

            return {
                "status": "completed",
                "message": "Exportation terminée",
                "total_emails": index_data.get("total_emails", 0),
                "total_batches": index_data.get("total_batches", 0),
                "export_date": index_data.get("export_date", ""),
                "mode": "real"
            }

        # Vérifier combien de fichiers batch existent
        batch_files = [f for f in os.listdir(export_dir)
                       if f.startswith("emails_batch_") and f.endswith(".json")]

        if batch_files:
            return {
                "status": "completed",
                "message": "Exportation terminée (sans fichier d'index)",
                "total_emails": None,
                "total_batches": len(batch_files),
                "mode": "real"
            }

        # Si aucun fichier batch n'est trouvé mais que le répertoire existe
        return {
            "status": "processing",
            "message": "Exportation en cours",
            "total_emails": 0,
            "total_batches": 0,
            "mode": "real"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def get_user_emails(
        email: str = Query(...),
        batch_number: Optional[int] = Query(None),
        authorization: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Récupère les emails exportés pour un utilisateur spécifique
    """
    try:
        # Vérification du token JWT
        try:
            payload = jwt.decode(authorization.credentials, SECRET_KEY, algorithms=[ALGORITHM])
            token_email = payload.get("email")

            # Vérifier que l'email du token correspond à l'email demandé
            if token_email != email:
                raise HTTPException(status_code=403, detail="Accès non autorisé")
        except JWTError:
            raise HTTPException(status_code=401, detail="Token invalide")

        # Récupérer le chemin du répertoire pour cet utilisateur
        user_id = normalize_email_for_storage(email)
        export_dir = get_file_path(f"backend/app/data")

        # Vérifier si le répertoire existe
        if not os.path.exists(export_dir):
            raise HTTPException(
                status_code=404,
                detail="Aucune donnée d'email exportée trouvée. Veuillez d'abord exporter vos emails."
            )

        # Si un numéro de lot spécifique est demandé
        if batch_number is not None:
            batch_file = os.path.join(export_dir, f"emails_batch_{batch_number}.json")
            if not os.path.exists(batch_file):
                raise HTTPException(status_code=404, detail=f"Lot d'emails {batch_number} non trouvé")

            with open(batch_file, "r", encoding="utf-8") as f:
                emails = json.load(f)

            return emails

        # Sinon, charger tous les fichiers batch
        emails = []
        batch_files = [f for f in os.listdir(export_dir)
                       if f.startswith("emails_batch_") and f.endswith(".json")]

        if not batch_files:
            raise HTTPException(
                status_code=404,
                detail="Aucun fichier d'emails trouvé dans le répertoire d'exportation."
            )

        # Trier les fichiers batch par numéro
        batch_files.sort(key=lambda x: int(x.split("_")[-1].split(".")[0]))

        # Charger chaque fichier batch
        for batch_file in batch_files:
            batch_path = os.path.join(export_dir, batch_file)
            with open(batch_path, "r", encoding="utf-8") as f:
                batch_emails = json.load(f)
                emails.extend(batch_emails)

        return emails
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/classified")
async def get_classified_emails(
        email: str = Query(...),
        batch_number: Optional[int] = Query(None),
        output_dir: Optional[str] = Query(None),
        authorization: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Récupère les emails classifiés pour un utilisateur spécifique
    """
    try:
        # Vérification du token JWT
        try:
            payload = jwt.decode(authorization.credentials, SECRET_KEY, algorithms=[ALGORITHM])
            token_email = payload.get("email")

            # Vérifier que l'email du token correspond à l'email demandé
            if token_email != email:
                raise HTTPException(status_code=403, detail="Accès non autorisé")
        except JWTError:
            raise HTTPException(status_code=401, detail="Token invalide")

        # Récupérer les emails (on réutilise la fonction précédente)
        if batch_number is not None:
            emails = await get_user_emails(email=email, batch_number=batch_number, authorization=authorization)
        else:
            emails = await get_user_emails(email=email, authorization=authorization)

        # Vérifier si les emails ont été classifiés
        has_classification = any(
            "accord_main_class" in email for email in emails[:10]
        ) if emails else False

        if not has_classification:
            raise HTTPException(
                status_code=404,
                detail="Les emails n'ont pas encore été classifiés. Veuillez attendre que le processus de classification soit terminé."
            )

        return {
            "total_emails": len(emails),
            "emails": emails
        }
    except HTTPException:
        # Rethrow HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))