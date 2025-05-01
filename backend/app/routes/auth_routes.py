from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from fastapi.responses import RedirectResponse, JSONResponse
import os
from backend.app.core.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from backend.app.email_providers.google.email_utils import normalize_email_for_storage
from backend.app.email_providers.google.gmail_auth import GmailAuthManager
from backend.app.services.flow_demarrage import flowDemarrage
from fastapi import BackgroundTasks, Body
from typing import Optional
from backend.app.services.export_status import check_export_status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from backend.app.core.config import settings
from fastapi import APIRouter, Query, Request, HTTPException, status, Depends

router = APIRouter(prefix="/auth")

# Initialize GmailAuthManager
auth_manager = GmailAuthManager()

# Dictionary to store authentication events
auth_completion_events = {}

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: Optional[str] = None
    service: Optional[str] = "google"


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Endpoint for standard OAuth2 token generation.
    This could be used for a username/password login flow in the future.
    """
    # This is a placeholder - you would normally validate user credentials here
    user_data = {"email": form_data.username}

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data=user_data, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/google/token")
async def google_login_token(user_data: dict = Body(...)):
    """
    Endpoint to generate a JWT token after Google OAuth authentication.
    Called by the frontend after Google authentication is complete.
    """
    if "email" not in user_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required"
        )

    email = user_data["email"]
    user_id = normalize_email_for_storage(email)

    # Verify that the user is authenticated with Google
    if not auth_manager.is_authenticated(user_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated with Google"
        )

    # Create and return JWT token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"email": email, "user_id": user_id},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_email": email
    }


@router.get("/gmail")
async def gmail_auth(request: Request, email: str = Query(None)):
    try:
        # Generate a user ID
        if email:
            user_id = normalize_email_for_storage(email)
        else:
            # Use "gmail" as the user_id for simplicity
            user_id = "gmail"

        print(f"Starting Gmail authentication for user_id: {user_id}")

        # Store the ID in the session
        request.session["user_id"] = user_id

        # Get authentication URL
        auth_url = auth_manager.get_auth_url(user_id)

        # Print debug info
        print(f"Generated auth URL: {auth_url[:50]}...")

        return {"auth_url": auth_url}
    except Exception as e:
        error_message = f"Error during Gmail authentication: {str(e)}"
        print(error_message)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_message)


@router.get("/callback")
async def auth_callback(request: Request, code: str = Query(...), state: str = Query(...)):
    """Handle Google OAuth callback."""
    try:
        print(f"OAuth callback received with state: {state}")
        print(f"Session user_id: {request.session.get('user_id')}")

        # Retrieve user ID
        user_id = state

        # Debug the token directory and expected file path
        tokens_dir = auth_manager.tokens_dir
        flow_path = os.path.join(tokens_dir, f"{user_id}_flow.json")
        print(f"Looking for flow file at: {flow_path}")
        print(f"Directory exists: {os.path.exists(tokens_dir)}")
        print(f"File exists: {os.path.exists(flow_path)}")

        # Process authorization code
        result = auth_manager.handle_callback(code, state)

        # Store email in session
        email = None
        if result and "email" in result:
            request.session["user_email"] = result["email"]
            email = result["email"]

        frontend_url = "http://localhost:3000/auth/callback"
        redirect_url = f"{frontend_url}?code={code}&email={email or ''}&service=gmail"

        # Set authentication completion flag
        key = email or "last_auth"
        auth_completion_events[key] = True

        return RedirectResponse(url=redirect_url)

    except Exception as e:
        error_message = f"Error during authentication callback: {str(e)}"
        print(error_message)
        import traceback
        traceback.print_exc()

        # Return a more helpful error response
        return JSONResponse(
            status_code=500,
            content={"error": error_message}
        )


security = HTTPBearer(auto_error=False)


@router.get("/status")
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


@router.post("/complete")
async def auth_complete(email: str = None):
    """Endpoint appelé pour signaler que l'authentification est terminée"""
    key = email or "last_auth"
    auth_completion_events[key] = True
    return {"status": "success", "message": "Authentification terminée avec succès"}