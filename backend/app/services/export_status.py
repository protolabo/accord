import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from backend.app.utils.absolute_path import get_file_path

# absolute path
STATUS_DIR = get_file_path("backend/app/data/export_status")


def ensure_status_directory():
    """Crée le répertoire de statut s'il n'existe pas"""
    os.makedirs(STATUS_DIR, exist_ok=True)


def get_status_file_path(email: str) -> str:
    safe_email = email.replace("@", "_at_").replace(".", "_dot_")
    return os.path.join(STATUS_DIR, f"{safe_email}_status.json")


def update_export_status(email: str, status: str, message: str = "", progress: int = 0,
                         extra_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Met à jour le statut d'exportation pour un email donné

    Args:
        email: L'adresse email de l'utilisateur
        status: Le statut actuel ('not_started', 'processing', 'completed', 'error')
        message: Un message descriptif sur l'état actuel
        progress: Pourcentage de progression (0-100)
        extra_data: Données supplémentaires à stocker

    Returns:
        Dict avec le statut mis à jour
    """
    ensure_status_directory()

    status_data = {
        "email": email,
        "status": status,
        "message": message,
        "progress": progress,
        "updated_at": time.time(),
        "extra": extra_data or {}
    }

    # Écrire le statut dans un fichier
    with open(get_status_file_path(email), 'w', encoding='utf-8') as f:
        json.dump(status_data, f, ensure_ascii=False, indent=2)

    return status_data


def check_export_status(email: str) -> Dict[str, Any]:
    """
    Vérifie le statut actuel du processus d'exportation pour un email donné

    Args:
        email: L'adresse email de l'utilisateur

    Returns:
        Dict contenant les informations de statut actuelles
    """
    status_file = get_status_file_path(email)

    # Si le fichier n'existe pas, l'exportation n'a pas commencé
    if not os.path.exists(status_file):
        return {
            "email": email,
            "status": "not_started",
            "message": "L'exportation n'a pas encore commencé",
            "progress": 0,
            "updated_at": time.time(),
            "extra": {}
        }

    # Lire le statut depuis le fichier
    try:
        with open(status_file, 'r', encoding='utf-8') as f:
            status_data = json.load(f)

        # Vérifier si les données sont complètes et valides
        required_fields = ["status", "message", "progress", "updated_at"]
        if not all(field in status_data for field in required_fields):
            # Fichier de statut incomplet, retourner un statut par défaut
            return {
                "email": email,
                "status": "unknown",
                "message": "Données de statut incomplètes",
                "progress": 0,
                "updated_at": time.time(),
                "extra": {}
            }

        return status_data

    except (json.JSONDecodeError, IOError) as e:
        # Erreur de lecture du fichier
        return {
            "email": email,
            "status": "error",
            "message": f"Erreur lors de la lecture du statut: {str(e)}",
            "progress": 0,
            "updated_at": time.time(),
            "extra": {}
        }


def clear_export_status(email: str) -> bool:
    """
    Supprime le fichier de statut d'exportation pour un email

    Args:
        email: L'adresse email de l'utilisateur

    Returns:
        True si le fichier a été supprimé, False sinon
    """
    status_file = get_status_file_path(email)

    if os.path.exists(status_file):
        os.remove(status_file)
        return True
    return False