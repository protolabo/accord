from fastapi import APIRouter, Query, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.responses import HTMLResponse
import uuid
from backend.app.email_providers.google.email_utils import normalize_email_for_storage
from backend.app.email_providers.google.gmail_auth import GmailAuthManager
from backend.app.services.flow_demarrage import flowDemarrage
from fastapi import BackgroundTasks, Body
from typing import Optional
from backend.app.services.export_status import check_export_status
from fastapi import Header, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from backend.app.core.config import settings

# Configurer le routeur avec des options CORS
router = APIRouter()
auth_manager = GmailAuthManager()

# Modification de la route /export/gmail pour gérer explicitement les OPTIONS
@router.options("/export/gmail")
async def options_export_gmail():
    """Endpoint OPTIONS pour gérer les requêtes préflight CORS"""
    return {}

@router.post("/export/gmail")
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


@router.get("/export/gmail/status")
async def export_gmail_status(email: str = Query(...)):
    """Endpoint pour vérifier le statut d'un export Gmail"""
    status_data = check_export_status(email)
    return status_data


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

        # Rediriger vers Google, important si on veut tester que le backend
        #return RedirectResponse(auth_url)

        return {"auth_url": auth_url}

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
        email = None
        if result and "email" in result:
            request.session["user_email"] = result["email"]
            email = result["email"]

        frontend_url = "http://localhost:3000/auth/callback"
        redirect_url = f"{frontend_url}?code={code}&email={email or ''}&service=gmail"

        # Créer l'événement d'authentification terminée
        key = email or "last_auth"
        auth_completion_events[key] = True

        return RedirectResponse(url=redirect_url)

    except Exception as e:
        error_message = f"Erreur lors du callback d'authentification: {str(e)}"
        print(error_message)
        raise HTTPException(status_code=500, detail=error_message)


security = HTTPBearer(auto_error=False)


@router.get("/auth/status")
async def auth_status(
        request: Request,
        email: str = Query(None),
        authorization: HTTPAuthorizationCredentials = Depends(security)
):
    """Vérifie le statut d'authentification d'un utilisateur."""
    try:
        # Vérifier d'abord si un token JWT est fourni
        if authorization:
            try:
                # Décodez le token JWT
                payload = jwt.decode(
                    authorization.credentials,
                    settings.SECRET_KEY,
                    algorithms=[settings.ALGORITHM]
                )

                # Extraire l'email du token
                token_email = payload.get("email")

                if token_email:
                    # Utiliser l'email du token pour l'authentification
                    user_id = normalize_email_for_storage(token_email)
                    is_authenticated = auth_manager.is_authenticated(user_id)

                    return {
                        "authenticated": is_authenticated,
                        "email": token_email,
                        "user_id": user_id
                    }
            except JWTError as e:
                print(f"Erreur JWT: {str(e)}")
                # Continuer avec d'autres méthodes si le JWT échoue

        # Si pas de JWT valide, utiliser la méthode par email comme avant
        if email:
            user_id = normalize_email_for_storage(email)
        else:
            # Sinon, essayer de récupérer l'email de la session
            email = request.session.get("user_email")
            if not email:
                return JSONResponse(
                    status_code=200,  # Utiliser 200 au lieu de 400 pour éviter les erreurs CORS
                    content={"authenticated": False, "message": "Aucun email fourni ou trouvé en session"}
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
        print(f"Erreur lors de la vérification du statut: {str(e)}")
        return JSONResponse(
            status_code=200,  # Utiliser 200 au lieu de 500 pour éviter les erreurs CORS
            content={"authenticated": False, "message": f"Erreur lors de la vérification: {str(e)}"}
        )



# Dictionnaire pour stocker les événements d'authentification
auth_completion_events = {}

@router.post("/auth/complete")
async def auth_complete(email: str = None):
    """Endpoint appelé pour signaler que l'authentification est terminée"""
    key = email or "last_auth"
    auth_completion_events[key] = True
    return {"status": "success", "message": "Authentification terminée avec succès"}

@router.get("/")
async def home():
    return RedirectResponse(url="/")