from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("all-MiniLM-L6-v2")


intent_descriptions = {
    "Meeting": "Proposing improvements to meeting formats, such as suggesting a specific time and a specific topic for discussions.",
    "Business activity": "Planning team-building activities like trips, sports, or social events."
}

intent_embeddings = {
    intent: model.encode(desc)
    for intent, desc in intent_descriptions.items()
}

def semantic_intent_detection(text, threshold=0.6):
    text_embedding = model.encode(text)
    print(text_embedding)
    scores = {}
    for intent, emb in intent_embeddings.items():
        similarity = util.cos_sim(text_embedding, emb).item()
        print(similarity)
        if similarity > threshold:
            scores[intent] = similarity
    return max(scores, key=scores.get) if scores else "Others"

email_text = "Traveling to have a business meeting takes the fun out of the trip.  Especially if you have to prepare a presentation.  I would suggest holding the business plan meetings here then take a trip without any formal business meetings.  I would even try and get some honest opinions on whether a trip is even desired or necessary.\n\nAs far as the business meetings, I think it would be more productive to try and stimulate discussions across the different groups about what is working and what is not.  Too often the presenter speaks and the others are quiet just waiting for their turn.   The meetings might be better if held in a round table discussion format.  \n\nMy suggestion for where to go is Austin.  Play golf and rent a ski boat and jet ski's.  Flying somewhere takes too much time."
print(semantic_intent_detection(email_text))