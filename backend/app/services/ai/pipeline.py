from backend.app.services.ai.emailPreprocess import sanitize_numbers, preprocess_email
from backend.app.services.ai.intentDetector import intent_classification
from backend.app.services.ai.subClassifier import sub_classification



def process_email(raw_email: dict) -> dict:
    """
    Traite un email brut et retourne sa classification.

    Args:
        raw_email (dict): Email brut au format dictionnaire

    Returns:
        dict: Classification de l'email avec les clés 'main_class' et 'sub_classes'
    """
    body = raw_email.get("Body", {})
    subject = raw_email.get("Subject", "")
    sender = raw_email.get("From", "")

    if body == "":
        body = {}
    if subject is None:
        subject = ""

    plain_text = body.get("plain", "") if isinstance(body, dict) else ""
    if plain_text is None:
        plain_text = ""

    sanitized_body = sanitize_numbers(plain_text)
    preprocessed = preprocess_email(sanitized_body, keep_paragraphs=False)

    email_to_classified = f'{subject} {preprocessed}'

    # Classification de l'intention (Action, Information, ou Threads par défaut)
    main_class = intent_classification(preprocessed, subject,sender)

    # Classification des sous-catégories
    sub_classes = sub_classification(email_to_classified)

    return {
        "main_class": main_class,
        "sub_classes": sub_classes
    }

 # Test
if __name__ == "__main__":
     # Exemple d'email
     test_email = {
         "From": "alexander.smith@gmail.com",
         "Subject": "Two-Factor Authentication Code",
         "Body": {
             "plain": "Hello Sheila,\n\nTo ensure that only you have attempted to log into your account, kindly confirm the below entry code: 468302. If this wasn't an action initiated by yourself, it could indicate unauthorized access.\n\nSecurity Team\n\n--\nAlexander Smith\nMarketing Director\nMarketing\nGmail\nTel: 745.591.7649x424"
         }
     }

     # Traiter l'email
     result = process_email(test_email)

     # Afficher les résultats
     print(result)
     print("Catégorie principale:", result["main_class"])
     print("Sous-catégories:", result["sub_classes"])