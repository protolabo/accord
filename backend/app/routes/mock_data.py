import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from backend.app.utils.absolute_path import get_file_path

router = APIRouter(prefix="/mock", tags=["mock"])


@router.get("/emails")
async def get_mock_emails():
    """
    Renvoie les emails mockés stockés dans le fichier JSON
    """
    try:
        file_path = get_file_path("backend/app/data/mockdata/emails.json")

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Fichier de données mockées non trouvé")

        with open(file_path, "r", encoding="utf-8") as f:
            mock_emails = json.load(f)

        return mock_emails
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/classified-emails/status")
async def get_classification_status():
    """Returns mock classification status"""
    return {
        "status": "completed",  # Always "completed" for mock data
        "mode": "mock",
        "total_emails": 875,
        "total_batches": 1
    }


@router.get("/classified-emails")
async def get_classified_emails():
    """Returns classified emails from your existing mock data"""
    try:
        # Reuse your existing function to get mock emails
        file_path = get_file_path("backend/app/data/mockdata/emails.json")
        with open(file_path, "r", encoding="utf-8") as f:
            mock_emails = json.load(f)

        return {
            "total_emails": len(mock_emails),
            "emails": mock_emails
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))