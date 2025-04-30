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