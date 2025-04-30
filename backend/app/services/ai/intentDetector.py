import re

def intent_classification(email_text, subject, sender):
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
    # en prod , il faut plutot placer useremail
    if sender != "alexander.smith@gmail.com" and any(keyword in email_lower for keyword in action_keywords):
        return ["Actions"]

    # Vérifier si c'est une information
    # en prod , il faut plutot placer useremail
    elif sender != "alexander.smith@gmail.com" and any(keyword in email_lower for keyword in info_keywords ):
        return ["Informations"]

    # Par défaut, c'est un thread
    else:
        return ["Threads"]