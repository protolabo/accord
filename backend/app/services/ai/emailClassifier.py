from sentence_transformers import SentenceTransformer, util
from sklearn.metrics.pairwise import cosine_similarity
import json

model = SentenceTransformer('paraphrase-mpnet-base-v2')


with open("category_desp.json", 'r', encoding='utf-8') as f:
    categories = json.load(f)

# Main class encoding
main_descriptions = {name: data["description"] for name, data in categories.items()}
main_texts = [f"{k}: {v}" for k, v in main_descriptions.items()]
main_embeddings = model.encode(main_texts)

# Subclass encoding
subcategory_embeddings = {}
for main_class, data in categories.items():
    sub_texts = [f"{k}: {v}" for k, v in data["subcategories"].items()]
    subcategory_embeddings[main_class] = model.encode(sub_texts)

# Hierarchical classification
def hierarchical_classify(email_text, main_threshold=0.15, sub_threshold=0.2):
    # Main class
    email_embed = model.encode([email_text])
    main_similarities = cosine_similarity(email_embed, main_embeddings)
    main_score = main_similarities.max()
    main_index = main_similarities.argmax()
    main_class = list(categories.keys())[main_index]
    
    if main_score < main_threshold:
        return {"main": "Uncertain", "sub": None}
    
    # Subclass
    sub_data = categories[main_class]["subcategories"]
    sub_names = list(sub_data.keys())
    sub_embeds = subcategory_embeddings[main_class]
    
    sub_sims = cosine_similarity(email_embed, sub_embeds)
    sub_score = sub_sims.max()
    sub_index = sub_sims.argmax()
    sub_class = sub_names[sub_index] if sub_score >= sub_threshold else None
    
    return {
        "main": main_class,
        "main_confidence": float(main_score),
        "sub": sub_class,
        "sub_confidence": float(sub_score)
    }


# # Test
# with open('./app/services/ai/testEmails.json', 'r', encoding='utf-8') as f:
#     email_data = json.load(f)

# results = []

# for email in email_data:
#     text = f"{email['subject']} {email['body']}"
#     # text = f"{email['body']}"
#     predicted_label, confidence = hierarchical_classify(text)
#     results.append({
#         "id": email["id"],
#         "subject": email["subject"],
#         "true_category": email.get("category", "N/A"),
#         "predicted_category": predicted_label,
#         "confidence": float(round(confidence, 4))
#     })

# with open('./app/services/ai/classified_emails.json', 'w', encoding='utf-8') as f_out:
#     json.dump(results, f_out, ensure_ascii=False, indent=2)
