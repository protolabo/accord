from sentence_transformers import SentenceTransformer, util
from sklearn.metrics.pairwise import cosine_similarity
import json
import os
import numpy as np

# Charger le modèle de transformer
model = SentenceTransformer('paraphrase-mpnet-base-v2')

current_dir = os.path.dirname(os.path.abspath(__file__))
categories_path = os.path.join(current_dir, "category_desp.json")

with open(categories_path, 'r', encoding='utf-8') as f:
    categories = json.load(f)

# Encoder les descriptions des catégories principales et des sous-catégories
main_descriptions = {name: data["description"] for name, data in categories.items()}
main_texts = [f"{k}: {v}" for k, v in main_descriptions.items()]
main_embeddings = model.encode(main_texts)

# Encoder les sous-catégories
subcategory_embeddings = {}
subcategory_names = {}
for main_class, data in categories.items():
    sub_texts = [f"{k}: {v}" for k, v in data["subcategories"].items()]
    subcategory_embeddings[main_class] = model.encode(sub_texts)
    subcategory_names[main_class] = list(data["subcategories"].keys())



def sub_classification(email_text, main_threshold=0.08, sub_threshold=0.15, top_k=3):
    """
    Classifie un email en sous-catégories en utilisant les embeddings.
    Seuils réduits pour permettre plus de correspondances.
    """
    # Encoder le contenu de l'email
    email_embed = model.encode([email_text])

    # Choisir la classe principale
    main_sims = cosine_similarity(email_embed, main_embeddings)[0]

    valid_idxs = sorted(
        [i for i, s in enumerate(main_sims) if s >= main_threshold],
        key=lambda i: -main_sims[i]
    )[:top_k]

    if not valid_idxs:
        valid_idxs = [np.argmax(main_sims)]

    candidate_mains = [list(categories.keys())[i] for i in valid_idxs]

    dynamic_sub_embeds = []
    dynamic_sub_info = []

    for main_name in candidate_mains:
        sub_embeds = subcategory_embeddings.get(main_name, [])
        sub_names = subcategory_names.get(main_name, [])
        dynamic_sub_embeds.extend(sub_embeds)
        dynamic_sub_info.extend([(main_name, sub_name) for sub_name in sub_names])

    if not dynamic_sub_embeds:
        for main_name in categories.keys():
            sub_embeds = subcategory_embeddings.get(main_name, [])
            sub_names = subcategory_names.get(main_name, [])
            dynamic_sub_embeds.extend(sub_embeds)
            dynamic_sub_info.extend([(main_name, sub_name) for sub_name in sub_names])

    if not dynamic_sub_embeds:
        return []

    sub_sims = cosine_similarity(email_embed, dynamic_sub_embeds)[0]

    # Choisir toutes les sous-classes dont la similarité est supérieure au seuil
    top_indices = sorted(range(len(sub_sims)), key=lambda i: sub_sims[i], reverse=True)[:5]
    valid_subs = []

    for idx in top_indices:
        score = sub_sims[idx]
        if score >= sub_threshold:
            _, sub_class = dynamic_sub_info[idx]
            valid_subs.append([sub_class, float(score)])

    # S'assurer qu'au moins une sous-catégorie est renvoyée
    if not valid_subs and len(top_indices) > 0:
        best_idx = top_indices[0]
        _, sub_class = dynamic_sub_info[best_idx]
        valid_subs.append([sub_class, float(sub_sims[best_idx])])

    return valid_subs