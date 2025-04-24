from backend.app.services.ai.emailPreprocess import sanitize_numbers, preprocess_email
from backend.app.services.ai.emailClassifier import email_classification
import json

def process_email(raw_email: dict) -> dict:
    body = raw_email.get("Body", {})
    plain_text = body.get("plain", "") if isinstance(body, dict) else ""
    sanitized_body = sanitize_numbers(plain_text)
    preprocessed = preprocess_email(sanitized_body, keep_paragraphs=False)
    email_to_classified = f'{raw_email.get("Subject", "")} {preprocessed}'
    cls = email_classification(email_to_classified)
    return {
        "main_class": cls["main_class"],
        "sub_classes": cls["sub_classes"]
    }

# # Test
# with open('data/mock_emails.json', 'r', encoding='utf-8') as f:
#     email_data = json.load(f)

# results = []

# for email in email_data:
#     predicted_result = process_email(email)
#     results.append({
#         "id": email.get("id", ""),
#         "subject": email.get("subject", ""),
#         "body": email.get("body", ""),
#         "mains": predicted_result["main_class"],
#         "subs": predicted_result["sub_classes"]
#     })

# with open('data/mock_emails_predicted.json', 'w', encoding='utf-8') as f_out:
#     json.dump(results, f_out, ensure_ascii=False, indent=2)