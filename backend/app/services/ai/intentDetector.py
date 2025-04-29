import re

def intent_classification(email_text, subject):
    """
    Classifie l'intention d'un email selon trois catégories:
    - Actions: messages nécessitant une action spécifique
    - Informations: messages purement informatifs
    - Threads: catégorie par défaut pour tous les autres messages
    """
    # Détection des demandes d'action
    action_keywords = ["confirm", "confirmer", "validate", "valider", "approve", "répondre",
                       "payer", "register", "inscrire", "rendez-vous", "meeting", "réunion"]

    # Détection des informations
    info_keywords = ["update", "mise à jour", "notification", "politique", "newsletter",
                     "announcement", "annonce", "information", "reminder", "rappel"]

    email_lower = (subject + " " + email_text).lower()

    # Vérifier si c'est une action
    if any(keyword in email_lower for keyword in action_keywords):
        return ["Action"]

    # Vérifier si c'est une information
    elif any(keyword in email_lower for keyword in info_keywords):
        return ["Informations"]

    # Par défaut, c'est un thread
    else:
        return ["Threads"]