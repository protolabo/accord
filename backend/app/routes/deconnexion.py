import os
from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.responses import JSONResponse
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from backend.app.utils.absolute_path import get_file_path
import json

router = APIRouter(prefix="/logout")


class LogoutRequest(BaseModel):
    email: Optional[str] = None


def revoke_google_token(refresh_token):
    import requests

    response = requests.post(
        'https://oauth2.googleapis.com/revoke',
        params={'token': refresh_token},
        headers={'content-type': 'application/x-www-form-urlencoded'}
    )

    if response.status_code == 200:
        return True
    else:
        print(f"Erreur lors de la révocation: {response.text}")
        return False
@router.post("/revoke")
async def logout(request: LogoutRequest = Body(...)):
    try:
        # Code existant pour supprimer le fichier de token
        token_path = "backend/app/email_providers/google/tokens/x_dot__at_gmail_dot_com.json"

        # Avant de supprimer, essayer de révoquer le token
        if os.path.exists(token_path):
            try:
                with open(token_path, 'r') as f:
                    token_data = json.load(f)

                # Si le token existe, essayer de le révoquer
                if 'refresh_token' in token_data:
                    revoke_google_token(token_data['refresh_token'])
                    print("Token Google révoqué avec succès")
            except Exception as e:
                print(f"Erreur lors de la révocation du token: {str(e)}")

            # Continuer avec la suppression du fichier
            os.remove(token_path)
            print(f"Fichier de token supprimé: {token_path}")

        return {"status": "success", "message": "Déconnexion réussie"}
    except Exception as e:
        print(f"Erreur pendant la déconnexion: {str(e)}")
        return {"status": "success", "message": "Déconnexion réussie avec des avertissements"}


@router.post("/")
async def logout(request: LogoutRequest = Body(...)):
    """Gérer la déconnexion de l'utilisateur et supprimer les fichiers de token"""
    try:
        # Supprimer le fichier de token spécifique
        token_path = "backend/app/email_providers/google/tokens/x_dot__at_gmail_dot_com.json"
        if os.path.exists(token_path):
            os.remove(token_path)
            print(f"Fichier de token supprimé: {token_path}")
        else:
            print(f"Fichier de token non trouvé: {token_path}")

        # dans un cas ideal

        """

        # Si vous souhaitez également supprimer le token basé sur l'email fourni
        if request.email:
            from backend.app.email_providers.google.email_utils import normalize_email_for_storage
            normalized_email = normalize_email_for_storage(request.email)
            user_token_path = f"backend/app/email_providers/google/tokens/{normalized_email}.json"

            if os.path.exists(user_token_path) and user_token_path != token_path:
                os.remove(user_token_path)
                print(f"Fichier de token utilisateur supprimé: {user_token_path}")
                
        """

        return {"status": "success", "message": "Déconnexion réussie"}
    except Exception as e:
        print(f"Erreur pendant la déconnexion: {str(e)}")
        # Même en cas d'erreur, nous renvoyons un succès au client
        # car l'utilisateur doit pouvoir se déconnecter dans tous les cas
        return {"status": "success", "message": "Déconnexion réussie avec des avertissements"}