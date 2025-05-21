import os
import json
import logging
from typing import Dict, Any, Optional
import torch
from pathlib import Path

logger = logging.getLogger(__name__)

# Valeurs par défaut
# s'assurer que  le fichier .gguf est deja telecharger et aussi changer le chemin d'acces
# la longueur du context doit etre ajuster
DEFAULT_CONFIG = {
    "llm": {
        "model_type": "gguf",
        "model_path": "H:\\llm\\lmstudio\\lmstudio-community\\Mistral-7B-Instruct-v0.3-GGUF\\Mistral-7B-Instruct-v0.3-Q4_K_M.gguf",
        "max_new_tokens": 512,
        "temperature": 0.1,
        "top_p": 0.9,
        "context_length": 2048
    },
    "parsing": {
        "timeout_ms": 2000,
        "retry_count": 2
    },
    "execution": {
        "timeout_ms": 500,
        "max_concurrent": 5
    },
    "cache": {
        "enabled": True,
        "ttl_seconds": 3600,
        "max_size": 1000
    }
}

# Chargement de la configuration
# Configuration active
_CONFIG = DEFAULT_CONFIG.copy()

def get_config():
    """Récupère la configuration actuelle"""
    return _CONFIG


def get_llm_config():
    """
    Initialise et retourne l'instance du LLM selon la configuration

    Returns:
        LLM: Instance configurée du modèle de langage
    """
    from langchain.llms import CTransformers
    import logging

    logger = logging.getLogger(__name__)
    config = _CONFIG["llm"]

    logger.info(f"Initialisation du LLM GGUF depuis: {config['model_path']}")

    try:
        # Créer l'instance avec CTransformers pour GGUF
        llm = CTransformers(
            model=config["model_path"],
            model_type="mistral",
            max_new_tokens=config["max_new_tokens"],
            temperature=config["temperature"],
            top_p=config["top_p"],
            context_length=config["context_length"]
        )

        return llm

    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation du LLM GGUF: {str(e)}")
        raise RuntimeError(f"Impossible d'initialiser le LLM: {str(e)}")


