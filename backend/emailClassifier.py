from sentence_transformers import SentenceTransformer, util
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer('paraphrase-mpnet-base-v2')


category_descriptions = {
    "Project Communication": "Discussions related to specific projects, including progress updates, task assignments, risk alerts, and resource coordination. Typically contains project names, milestones, deliverables, and attachments like requirements documents.",
    "Meeting Scheduling": "Invitations or updates for meetings, containing time/location (physical/virtual), agenda, participant list, and conference links (Zoom/Teams). May include rescheduling or cancellation notices.",
    "Task Assignment": "Clear instructions assigning responsibilities with deadlines, priority levels (P0/P1), and expected deliverables. Often references task tracking tools like JIRA or Trello.",
    "Client Communication": "External communications with clients or partners, covering contract negotiations, requirements confirmation, service agreements, or issue resolution.",
    "Internal Announcements": "Company-wide policy updates, organizational changes, HR notifications, or department-wide announcements requiring employee acknowledgment.",
    "Job Applications": "Emails related to hiring processes, including interview scheduling, offer letters, resume submissions, or recruitment campaign notifications.",
    "File Collaboration": "Sharing documents via cloud storage links (Google Drive, OneDrive) or collaborative editing requests, often with version control and access permissions."
}

# Encoder les Decriptions des classes
category_names = list(category_descriptions.keys())
category_texts = [f"{name}: {desc}" for name, desc in category_descriptions.items()]
category_embeddings = model.encode(category_texts)

# Fonction de classification
def classify_email(email_text, threshold=0.3):
    email_embedding = model.encode([email_text])
    
    # Calculer similarite
    similarities = cosine_similarity(email_embedding, category_embeddings)
    
    # Acquerir le meilleur score
    max_score = similarities.max()
    best_index = similarities.argmax()
    
    if max_score < threshold:
        return "Unclassified", max_score
    else:
        return category_names[best_index], max_score

# Test
sample_email = "Traveling to have a business meeting takes the fun out of the trip.  Especially if you have to prepare a presentation.  I would suggest holding the business plan meetings here then take a trip without any formal business meetings.  I would even try and get some honest opinions on whether a trip is even desired or necessary.\n\nAs far as the business meetings, I think it would be more productive to try and stimulate discussions across the different groups about what is working and what is not.  Too often the presenter speaks and the others are quiet just waiting for their turn.   The meetings might be better if held in a round table discussion format.  \n\nMy suggestion for where to go is Austin.  Play golf and rent a ski boat and jet ski's.  Flying somewhere takes too much time."

predicted_class, confidence = classify_email(sample_email)
print(f"Predicted: {predicted_class} (Confidence: {confidence:.2f})")
