from fastapi import APIRouter, Query, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.responses import HTMLResponse
import uuid
from backend.app.services.flow_demarrage import flowDemarrage
from fastapi import BackgroundTasks, Body
from typing import Optional
from backend.app.services.export_status import check_export_status


router = APIRouter(prefix="/export")


@router.options("/gmail")
async def options_export_gmail():
    """Endpoint OPTIONS pour gérer les requêtes préflight CORS"""
    return {}


@router.post("/gmail")
async def export_gmail(
        background_tasks: BackgroundTasks,
        email: str = Body(...),
        max_emails: Optional[int] = Body(None),
        output_dir: Optional[str] = Body("../data"),
        batch_size: Optional[int] = Body(5000)
):
    """Endpoint pour déclencher l'export des emails Gmail"""
    background_tasks.add_task(
        flowDemarrage,
        email=email,
        max_emails=max_emails,
        output_dir=output_dir,
        batch_size=batch_size
    )

    return {
        "message": f"Export des emails pour {email} démarré",
        "status": "processing",
        "output_directory": output_dir
    }


@router.get("/gmail/status")
async def export_gmail_status(email: str = Query(...)):
    """Endpoint pour vérifier le statut d'un export Gmail"""
    status_data = check_export_status(email)
    return status_data