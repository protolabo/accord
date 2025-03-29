import networkx as nx
import matplotlib.pyplot as plt
import json
import os

# Chemins vers les fichiers
file_names = [
    "emails_batch_1.json",
    "emails_batch_2.json",
    "emails_batch_3.json",
    "emails_batch_4.json",
    "emails_batch_5.json"
]

# Création du graphe
G = nx.Graph()

# Fonction pour ajouter les arêtes au graphe
def add_edges_from_mail(mail):
    sender = mail["From"].strip().lower()
    recipients = []

    if mail.get("To"):
        recipients += [r.strip().lower() for r in mail["To"].split(",") if r.strip()]
    if mail.get("Cc"):
        recipients += [r.strip().lower() for r in mail["Cc"].split(",") if r.strip()]
    if mail.get("Bcc"):
        recipients += [r.strip().lower() for r in mail["Bcc"].split(",") if r.strip()]

    for recipient in recipients:
        if sender and recipient:
            if G.has_edge(sender, recipient):
                G[sender][recipient]["weight"] += 1
            else:
                G.add_edge(sender, recipient, weight=1)

# Traitement de tous les fichiers
for file_name in file_names:
    if os.path.exists(file_name):
        with open(file_name, "r", encoding="utf-8") as f:
            data = json.load(f)
            for mail in data:
                add_edges_from_mail(mail)

# Dessin du graphe
plt.figure(figsize=(12, 10))
pos = nx.spring_layout(G, k=0.5, seed=42)
edges = G.edges(data=True)
weights = [d['weight'] for (u, v, d) in edges]

nx.draw(G, pos, with_labels=True, node_color='lightblue', edge_color='gray',
        node_size=1500, font_size=8, width=weights)
plt.title("Graphe de connexion des emails (pondéré par nombre de messages)")
plt.show()

