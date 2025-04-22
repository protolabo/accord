from sentence_transformers import SentenceTransformer, util
from sklearn.metrics.pairwise import cosine_similarity
import json
import numpy as np

model = SentenceTransformer('paraphrase-mpnet-base-v2')


with open("backend/app/services/ai/category_desp.json", 'r', encoding='utf-8') as f:
    categories = json.load(f)

# Main class encoding
main_descriptions = {name: data["description"] for name, data in categories.items()}
main_texts = [f"{k}: {v}" for k, v in main_descriptions.items()]
main_embeddings = model.encode(main_texts)

# Subclass encoding
subcategory_embeddings = {}
subcategory_names = {}
for main_class, data in categories.items():
    sub_texts = [f"{k}: {v}" for k, v in data["subcategories"].items()]
    subcategory_embeddings[main_class] = model.encode(sub_texts)
    subcategory_names[main_class] = list(data["subcategories"].keys())

# Method for classification: Hierarchical Classification 
def hierarchical_classify(email_text, main_threshold=0.10, sub_threshold=0.2, top_k=2):
    # Encode email content
    email_embed = model.encode([email_text])

    # Choose main class
    main_sims = cosine_similarity(email_embed, main_embeddings)[0]

    valid_idxs = sorted(
        [i for i, s in enumerate(main_sims) if s >= main_threshold],
        key=lambda i: -main_sims[i]
    )[:top_k]

    if not valid_idxs:
        return {"mains": [], "subs": []}
    candidate_mains = [(list(categories.keys())[i], float(main_sims[i])) for i in valid_idxs]

    # Choose sub class
    dynamic_sub_embeds = []
    dynamic_sub_info = []

    for main_name, _ in candidate_mains:
        sub_embeds = subcategory_embeddings[main_name]
        sub_names = subcategory_names[main_name]
        dynamic_sub_embeds.extend(sub_embeds)
        dynamic_sub_info.extend([(main_name, sub_name) for sub_name in sub_names])
    
    if not dynamic_sub_embeds:
        return {"mains": candidate_mains, "subs": []}
    
    sub_sims = cosine_similarity(email_embed, dynamic_sub_embeds)[0]

    # Choose all subclass higher than threshold
    top5_indices = sorted(range(len(sub_sims)), key=lambda i: sub_sims[i], reverse=True)[:5]
    valid_subs = []
    for idx in top5_indices:
        score = sub_sims[idx]
        if score >= sub_threshold:
            main_class, sub_class = dynamic_sub_info[idx]
            valid_subs.append({
                "main_class": main_class,
                "sub_class": sub_class,
                "confidence": float(score)
            })

    valid_subs = sorted(valid_subs, key=lambda x: -x["confidence"])

    return {
        "mains": candidate_mains,  
        "subs": valid_subs
    }

# Email classification
def email_classification(email_text, diff_threshold=0.05):
    classification_result = hierarchical_classify(email_text)
    mains = classification_result.get("mains", [])
    main_names = [name for name, _ in mains]
    subs = classification_result.get("subs", [])

    # Return only main class if a Spam class is detected and return other if no sub class classified
    if "Spam" in main_names:
        return {"main_class": main_names, "sub_classes": []}
    elif not subs:
        return {"main_class": ["Other class"], "sub_classes": []}

    # Choose subs only within a threshold of the highest sub class
    subs_sorted = sorted(subs, key=lambda x: x["confidence"], reverse=True)
    highest_conf = subs_sorted[0]["confidence"]

    selected_subs = [sub for sub in subs_sorted if (highest_conf - sub["confidence"]) <= diff_threshold]

    main_classes = list(set([sub["main_class"] for sub in selected_subs]))
    sub_classes = [(sub["sub_class"],sub["confidence"]) for sub in selected_subs]

    return {"main_class": main_classes, "sub_classes": sub_classes}


# # Test
# with open('data/mock_emails.json', 'r', encoding='utf-8') as f:
#     email_data = json.load(f)

# results = []

# for email in email_data:
#     text = f'{email.get("subject", "")} {email.get("body", "")}'
#     predicted_result = email_classification(text)
#     results.append({
#         "id": email.get("message_id", ""),
#         "subject": email.get("subject", ""),
#         "body": email.get("body", ""),
#         "mains": predicted_result["main_class"],
#         "subs": predicted_result["sub_classes"]
#     })

# with open('data/mock_emails_predicted.json', 'w', encoding='utf-8') as f_out:
#     json.dump(results, f_out, ensure_ascii=False, indent=2)

