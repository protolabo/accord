from backend.app.services.ai.emailPreprocess import sanitize_numbers, preprocess_email
from backend.app.services.ai.emailClassifier import email_classification
from backend.app.services.ai.dateRecognition import choose_best_date

def process_email(raw_email: dict) -> dict:
    sanitized = sanitize_numbers(raw_email.get("body", ""))
    preprocessed = preprocess_email(sanitized, keep_paragraphs=False)
    cls = email_classification(preprocessed)
    date = choose_best_date(preprocessed)
    return {
        "main_class": cls["main_class"],
        "sub_classes": cls["sub_classes"],
        "recognized_date": date
    }