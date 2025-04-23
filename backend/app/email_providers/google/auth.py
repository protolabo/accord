from fastapi import APIRouter, Query, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.responses import HTMLResponse
import uuid
from backend.app.email_providers.google.email_utils import normalize_email_for_storage
from backend.app.email_providers.google.gmail_auth import GmailAuthManager
from backend.app.email_providers.google.export_gmail_to_json import export_emails_to_json
from fastapi import BackgroundTasks, Body
from typing import Optional

router = APIRouter()
auth_manager = GmailAuthManager()


@router.post("/export/gmail")
async def export_gmail(
        background_tasks: BackgroundTasks,
        email: str = Body(...),
        max_emails: Optional[int] = Body(None),
        output_dir: Optional[str] = Body("./data"),
        batch_size: Optional[int] = Body(5000)
):
    """Endpoint pour déclencher l'export des emails Gmail"""
    background_tasks.add_task(
        export_emails_to_json,
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
@router.get("/auth/gmail")
async def gmail_auth(request: Request, email: str = Query(None)):
    try:
        # Générer un ID utilisateur
        if email:
            user_id = normalize_email_for_storage(email)
        else:
            temp_id = str(uuid.uuid4())
            user_id = f"temp_{temp_id}"

        # Stocker l'ID dans la session
        request.session["user_id"] = user_id

        # Obtenir l'URL d'authentification
        auth_url = auth_manager.get_auth_url(user_id)

        # Rediriger vers Google
        return RedirectResponse(auth_url)

    except Exception as e:
        error_message = f"Erreur lors de l'authentification Gmail: {str(e)}"
        print(error_message)
        raise HTTPException(status_code=500, detail=error_message)

@router.get("/auth/callback")
async def auth_callback(request: Request, code: str = Query(...), state: str = Query(...)):
    """Gère le callback de Google OAuth."""
    try:
        # Récupérer l'ID utilisateur
        user_id = state

        # Vérifier la correspondance avec la session
        session_user_id = request.session.get("user_id")
        if session_user_id and session_user_id != user_id:
            print(f"Avertissement: ID de session ({session_user_id}) différent de l'ID d'état ({user_id})")

        # Traiter le code d'autorisation
        result = auth_manager.handle_callback(code, state)

        # Stocker l'email dans la session
        if result and "email" in result:
            request.session["user_email"] = result["email"]

        # Rediriger vers la page de succès
        frontend_success_url = "/auth-success"
        if result and "email" in result:
            frontend_success_url += f"?email={result['email']}"

        return RedirectResponse(url=frontend_success_url)

    except Exception as e:
        error_message = f"Erreur lors du callback d'authentification: {str(e)}"
        print(error_message)
        raise HTTPException(status_code=500, detail=error_message)

@router.get("/auth/status")
async def auth_status(request: Request, email: str = Query(None)):
    """Vérifie le statut d'authentification d'un utilisateur."""
    try:
        # Si email est fourni, l'utiliser pour vérifier le statut
        if email:
            user_id = normalize_email_for_storage(email)
        else:
            # Sinon, essayer de récupérer l'email de la session
            email = request.session.get("user_email")
            if not email:
                return JSONResponse(
                    status_code=400,
                    content={"authenticated": False, "message": "Aucun email fourni"}
                )
            user_id = normalize_email_for_storage(email)

        # Vérifier l'authentification
        is_authenticated = auth_manager.is_authenticated(user_id)

        return {
            "authenticated": is_authenticated,
            "email": email,
            "user_id": user_id
        }

    except Exception as e:
        error_message = f"Erreur lors de la vérification du statut d'authentification: {str(e)}"
        print(error_message)
        raise HTTPException(status_code=500, detail=error_message)

@router.get("/auth-success", response_class=HTMLResponse)
async def auth_success(request: Request, email: str = None):
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Authentification réussie - Accord</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                text-align: center;
            }}
            .success-container {{
                border-radius: 8px;
                background-color: #f9f9f9;
                padding: 30px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-top: 50px;
            }}
            h1 {{
                color: #2c7be5;
            }}
            .success-icon {{
                color: #28a745;
                font-size: 48px;
                margin-bottom: 20px;
            }}
            .button {{
                display: inline-block;
                background-color: #2c7be5;
                color: white;
                padding: 10px 20px;
                border-radius: 4px;
                text-decoration: none;
                margin-top: 20px;
                transition: background-color 0.3s;
            }}
            .button:hover {{
                background-color: #1a68d1;
            }}
        </style>
    </head>
    <body>
        <div class="success-container">
            <div class="success-icon">✓</div>
            <h1>Authentification réussie!</h1>
            <p>Votre compte <strong>{email or 'Gmail'}</strong> a été connecté avec succès à Accord.</p>
            <p>Vous pouvez maintenant accéder à vos emails et utiliser toutes les fonctionnalités de l'application.</p>
            <a href="/" class="button">Retour à l'application</a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.get("/")
async def home():
    return RedirectResponse(url="/")