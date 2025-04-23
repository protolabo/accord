def normalize_email_for_storage(email):
    """Normalise l'adresse email pour l'utiliser comme identifiant."""
    if not email:
        return ""
    return email.lower().strip().replace("@", "_at_").replace(".", "_dot_")