from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import json

# Choisir device cpu ou gpu
device = "cuda" if torch.cuda.is_available() else "cpu"

# Initialisation du modele pre-entraine
tokenizer = AutoTokenizer.from_pretrained("aglazkova/bart_finetuned_keyphrase_extraction")
model = AutoModelForSeq2SeqLM.from_pretrained("aglazkova/bart_finetuned_keyphrase_extraction").to(device)

# Read json file
with open('data\enron_emails.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

modified_data = []

# Predire classe
for item in data[:500]:
    email_body = item.get("body", "")

    if email_body.strip():
        tokenized_text = tokenizer(email_body, return_tensors="pt", max_length=120, truncation=True).to(device)
        translation = model.generate(**tokenized_text)
        translated_text = tokenizer.batch_decode(translation, skip_special_tokens=True)[0]
    else:
        translated_text = "No prediction"
    
    item["classe"] = translated_text
    modified_data.append(item)

with open('data\enron_emails_pred.json', 'w', encoding='utf-8') as file:
    json.dump(modified_data, file, indent=4, ensure_ascii=False)
