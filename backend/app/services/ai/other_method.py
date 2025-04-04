def subclass_classify(email_text, sub_threshold=0.2):
    email_embed = model.encode([email_text])
    
    dynamic_sub_embeds = []
    dynamic_sub_info = []
    for main_name, sub_embeds in subcategory_embeddings.items():
        sub_names = subcategory_names[main_name]
        dynamic_sub_embeds.extend(sub_embeds)
        dynamic_sub_info.extend([(main_name, sub_name) for sub_name in sub_names])
    
    if not dynamic_sub_embeds:
        return {"subs": []}
    
    sub_sims = cosine_similarity(email_embed, dynamic_sub_embeds)[0]
    
    valid_subs = []
    for idx, score in enumerate(sub_sims):
        if score >= sub_threshold:
            main_class, sub_class = dynamic_sub_info[idx]
            valid_subs.append({
                "main_class": main_class,
                "sub_class": sub_class,
                "confidence": float(score)
            })
    valid_subs = sorted(valid_subs, key=lambda x: -x["confidence"])
    
    return {"subs": valid_subs}