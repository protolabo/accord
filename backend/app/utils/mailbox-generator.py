import json
import random
import uuid
import base64
from datetime import datetime, timedelta
from faker import Faker
import os
import logging
from tqdm import tqdm


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("email_generation.log"),
        logging.StreamHandler()
    ]
)


faker_instances = [
    Faker('fr_FR'),
]

def get_fake():
    return random.choice(faker_instances)

def generate_realistic_email_content(topic, fake, is_reply=False):
    """
    Génère un contenu d'email professionnel cohérent basé sur le sujet
    """
    # Choix de paragraphes professionnels selon le sujet
    if "réunion" in topic.lower() or "invitation" in topic.lower() or "meeting" in topic.lower():
        paragraphs = [
            f"Je vous invite à participer à une réunion concernant {topic.split(':')[-1] if ':' in topic else topic}.",
            f"La réunion se tiendra le {fake.date_this_month().strftime('%d/%m/%Y')} à {fake.time('%H:%M')} dans la salle {fake.word().capitalize()}.",
            "Vous trouverez ci-joint l'ordre du jour proposé pour cette réunion.",
            "Merci de confirmer votre disponibilité pour cette date."
        ]
    elif "rapport" in topic.lower() or "bilan" in topic.lower() or "report" in topic.lower():
        paragraphs = [
            f"Veuillez trouver ci-joint le rapport sur {topic.split(':')[-1] if ':' in topic else 'les résultats récents'}.",
            f"Les points clés à retenir sont la progression de {fake.random_int(5, 25)}% sur le trimestre et l'optimisation des processus internes.",
            "Ces résultats seront présentés lors de la prochaine réunion d'équipe.",
            "N'hésitez pas à me contacter si vous avez des questions sur ces données."
        ]
    elif "budget" in topic.lower() or "finance" in topic.lower():
        paragraphs = [
            f"Suite à notre discussion sur le budget {topic.split(':')[-1] if ':' in topic else 'prévisionnel'}, voici les éléments demandés.",
            f"Le département financier a validé l'enveloppe de {fake.random_int(50, 500)}K€ pour ce projet.",
            "La répartition par poste de dépense est détaillée dans le document joint.",
            "Merci de me faire part de vos observations avant la fin de la semaine."
        ]
    elif "problème" in topic.lower() or "urgent" in topic.lower() or "issue" in topic.lower():
        paragraphs = [
            f"Nous avons identifié un problème important concernant {topic.split(':')[-1] if ':' in topic else 'le système'}.",
            f"L'équipe technique est mobilisée et travaille à une résolution dans les {fake.random_int(2, 24)} heures.",
            "Un plan d'action a été mis en place pour limiter l'impact sur nos activités.",
            "Je vous tiendrai informé de l'évolution de la situation."
        ]
    elif is_reply:
        paragraphs = [
            "Merci pour votre message.",
            f"Concernant votre demande à propos de {topic.replace('RE: ', '').replace('Re: ', '')}.",
            "Je vous confirme que nous pouvons prendre en compte votre requête et y donner suite rapidement.",
            "Je reste à votre disposition pour tout complément d'information."
        ]
    else:
        paragraphs = [
            f"Je me permets de vous contacter au sujet de {topic}.",
            "Suite à nos échanges précédents, j'aimerais vous proposer une approche structurée pour avancer sur ce dossier.",
            "Les documents nécessaires ont été préparés et sont disponibles pour votre consultation.",
            "Votre retour sur ces éléments sera précieux pour finaliser ce projet."
        ]
    
    return paragraphs

def generate_massive_dataset(total_emails=40_0000, batch_size=5000, output_dir="mock_data"):
    """
    
    Args:
        total_emails: Nombre total d'emails à générer
        batch_size: Taille de chaque lot
        output_dir: Répertoire de sortie
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # utilisateur principal
    primary_user = {
        "name": "Alexandre Dupont",
        "email": "alexandre.dupont@acmecorp.com",
        "position": "Directeur Marketing",
        "department": "Marketing",
        "company": "Acme Corporation"
    }
    
    logging.info(f"Génération d'emails pour la boîte mail de {primary_user['name']} ({primary_user['email']})")

    companies = []
    domains = []
    
    # Ajouter l'entreprise de l'utilisateur
    companies.append(primary_user["company"])
    domains.append("acmecorp.com")
    
    # Ajouter 29 autres entreprises
    for _ in range(29):
        fake = get_fake()
        company = fake.company()
        companies.append(company)
        domain = f"{company.lower().replace(' ', '').replace(',', '').replace('.', '')}.com"
        domains.append(domain)

    departments = [
        "Marketing", "Finance", "RH", "IT", "Ventes", "Support", "Direction",
        "Juridique", "R&D", "Production", "Logistique", "Communication",
        "Comptabilité", "Service Client", "Qualité", "Achats"
    ]

    logging.info("Génération de contacts professionnels...")
    contacts = []
    
    # Ajouter l'utilisateur principal aux contacts
    contacts.append(primary_user)
    
    # Ajouter des collègues ( domaine mail utilisateur =  domaine email)
    for i in range(50):
        fake = get_fake()
        first_name = fake.first_name()
        last_name = fake.last_name()
        dept = random.choice(departments)
        
        email = f"{first_name.lower()}.{last_name.lower()}@acmecorp.com"
        contacts.append({
            "name": f"{first_name} {last_name}",
            "email": email,
            "company": "Acme Corporation",
            "department": dept,
            "position": fake.job()
        })
    
    # Ajouter 149 contacts externes
    for i in range(149):
        fake = get_fake()
        company_idx = random.randint(1, len(companies) - 1)  # Exclure l'entreprise principale
        first_name = fake.first_name()
        last_name = fake.last_name()
        dept = random.choice(departments)
        domain = domains[company_idx]
        
        email = f"{first_name.lower()}.{last_name.lower()}@{domain}"
        contacts.append({
            "name": f"{first_name} {last_name}",
            "email": email,
            "company": companies[company_idx],
            "department": dept,
            "position": fake.job()
        })
    
    # Créer des projets fictifs
    projects = []
    for i in range(50):
        fake = get_fake()
        project_name = f"{fake.bs().capitalize()} {fake.word().capitalize()} Project"
        start_date = fake.date_between(start_date="-1y", end_date="-3m")
        end_date = fake.date_between(start_date=start_date, end_date="+6m")
        projects.append({
            "id": str(uuid.uuid4()),
            "name": project_name,
            "start_date": start_date,
            "end_date": end_date,
            "status": random.choice(["Planning", "In Progress", "Review", "Completed", "On Hold"]),
            "team": random.sample(contacts, random.randint(3, 8))
        })
    
    # Types d'extensions de fichiers pour les pièces jointes
    file_extensions = {
        "document": ["docx", "pdf", "xlsx", "pptx", "txt"],
        "image": ["jpg", "png", "gif"],
        "archive": ["zip", "rar"],
        "code": ["py", "js", "html", "css", "json"],
        "data": ["csv", "xml", "sql", "yaml"]
    }
    
    # Labels possibles pour les emails
    all_labels = [
        "INBOX", "IMPORTANT", "UNREAD", "SENT", "DRAFT",
        "CATEGORY_PERSONAL", "CATEGORY_PROMOTIONS", "CATEGORY_SOCIAL",
        "CATEGORY_UPDATES", "CATEGORY_FORUMS", "STARRED"
    ]
    
    # Catégories pour la classification des emails
    categories = [
        "Urgent", "Suivi", "Projet", "Administratif", "Client",
        "Fournisseur", "Interne", "Externe", "Réunion", "Formation",
        "Document", "Rapport", "Demande", "Action Requise", "FYI",
        "Planification", "Budget", "Technique", "Problème", "Solution"
    ]
    
    # Générer un grand nombre de threads   ( ~ 5 emails par thread)
    thread_count = total_emails // 5
    logging.info(f"Création de {thread_count} threads d'emails...")
    thread_ids = [str(uuid.uuid4()) for _ in range(thread_count)]
    
    # Stocker les threads déjà démarrés pour la cohérence des réponses
    thread_data = {}  # {thread_id: {'subject': '...', 'participants': [...], 'last_email': {...}}}
    
    # Générer les emails par lots
    all_email_ids = set()
    current_date = datetime.now()
    start_date = current_date - timedelta(days=365)  # Emails sur 1 an
    
    total_batches = (total_emails + batch_size - 1) // batch_size
    
    for batch_num in range(total_batches):
        batch_start = batch_num * batch_size
        batch_end = min(batch_start + batch_size, total_emails)
        batch_size_actual = batch_end - batch_start
        
        logging.info(f"Génération du lot {batch_num + 1}/{total_batches} ({batch_size_actual} emails)...")
        
        # Générer ce lot d'emails
        emails = []
        for i in tqdm(range(batch_size_actual)):
            fake = get_fake()
            
            ## 40% d'emails envoyés, 60% d'emails reçus
            is_sent = random.random() < 0.4
            
            #  # 30% de nouveaux threads ou si aucun thread n'existe
            is_new_thread = random.random() > 0.7 or not thread_data

            if is_new_thread:
                thread_id = random.choice(thread_ids)
                while thread_id in thread_data:
                    thread_id = random.choice(thread_ids)
            else:
                thread_candidates = list(thread_data.keys())
                thread_id = random.choice(thread_candidates) if thread_candidates else random.choice(thread_ids)
            
            # Gérer les informations de ce thread
            if thread_id in thread_data:
                # Thread existant - utiliser les infos pour cohérence
                thread_info = thread_data[thread_id]
                subject = "RE: " + thread_info['subject'] if not thread_info['subject'].startswith("RE: ") else thread_info['subject']
                
                # Maintenir la conversation entre les mêmes participants
                participants = thread_info['participants']
                
                if is_sent:
                    # L'utilisateur principal répond
                    from_contact = primary_user
                    # Choisir un destinataire parmi les participants précédents
                    to_candidates = [p for p in participants if p["email"] != primary_user["email"]]
                    to_contact = random.choice(to_candidates) if to_candidates else random.choice([c for c in contacts if c["email"] != primary_user["email"]])
                else:
                    # Quelqu'un répond à l'utilisateur principal
                    to_contact = primary_user
                    # Choisir un expéditeur parmi les participants précédents
                    from_candidates = [p for p in participants if p["email"] != primary_user["email"]]
                    from_contact = random.choice(from_candidates) if from_candidates else random.choice([c for c in contacts if c["email"] != primary_user["email"]])
                
                is_reply = True
            else:
                # Nouveau thread
                is_reply = False
                
                # Sélectionner expéditeur et destinataire pour un nouveau thread
                if is_sent:
                    from_contact = primary_user
                    to_candidates = [c for c in contacts if c["email"] != primary_user["email"]]
                    to_contact = random.choice(to_candidates)
                else:
                    to_contact = primary_user
                    from_candidates = [c for c in contacts if c["email"] != primary_user["email"]]
                    from_contact = random.choice(from_candidates)

                # Sélectionner un projet aléatoire (75% de chance)
                related_project = random.choice(projects) if random.random() < 0.75 else None
                
                if related_project:
                    subject_templates = [
                        f"{related_project['name']}: Mise à jour du statut",
                        f"{related_project['name']} - Prochaines étapes",
                        f"Plan d'action: {related_project['name']}",
                        f"{related_project['name']} - Compte-rendu de réunion",
                        f"Urgent: {related_project['name']} - Blocage identifié",
                        f"Pour validation: Livrables {related_project['name']}"
                    ]
                    subject = random.choice(subject_templates)
                else:
                    subject_templates = [
                        "Demande d'information: {topic}",
                        "Invitation: Réunion {topic} du {date}",
                        "Suivi: {topic}",
                        "Urgent: {topic}",
                        "Compte-rendu: {topic}",
                        "Proposition: {topic}",
                        "{topic} - Pour validation",
                        "Mise à jour: {topic}"
                    ]
                    
                    topics = [
                        "Budget prévisionnel",
                        "Recrutement",
                        "Planning trimestriel",
                        "Migration serveurs",
                        "Audit interne",
                        "Plan marketing",
                        "Nouveaux locaux",
                        "Formation équipe",
                        "Problème technique",
                        "Demande client",
                        "Revue qualité",
                        "Process interne"
                    ]
                    
                    subject = random.choice(subject_templates).format(
                        topic=random.choice(topics),
                        date=fake.date_this_month().strftime("%d/%m")
                    )

                thread_data[thread_id] = {
                    'subject': subject,
                    'participants': [from_contact, to_contact],
                    'last_email': None
                }
            
            # Gérer la date - pour les réponses, s'assurer qu'elles sont après le dernier email du thread
            if is_reply and thread_data[thread_id]['last_email']:
                last_email_date = datetime.fromisoformat(thread_data[thread_id]['last_email']['Internal-Date'])
                min_date = last_email_date + timedelta(minutes=random.randint(5, 1440))  # Entre 5 min et 24h après
                if min_date > current_date:
                    min_date = last_email_date + timedelta(minutes=random.randint(5, 60))
                email_date = min_date
            else:
                # premier email d'un thread
                random_days = random.randint(0, 365)
                email_date = start_date + timedelta(days=random_days,
                                                  hours=random.randint(0, 23),
                                                  minutes=random.randint(0, 59))

            # Salutation
            salutations = [
                f"Bonjour {to_contact['name'].split()[0]},",
                f"Cher(e) {to_contact['name'].split()[0]},",
                "Bonjour à tous,",
                "Chers collègues,",
                f"Bonjour {to_contact['name']},",
                "Bonjour,"
            ]
            opening = random.choice(salutations)
            
            # Corps du message avec contenu cohérent
            content_paragraphs = generate_realistic_email_content(subject, fake, is_reply)
            
            # Conclusion
            closings = [
                "Cordialement,",
                "Bien à vous,",
                "Bien cordialement,",
                "Meilleures salutations,",
                "À bientôt,",
                "En vous remerciant par avance,"
            ]
            closing = random.choice(closings)
            
            # Assemblage des paragraphes
            paragraphs = [opening] + content_paragraphs + [closing]
            
            # Construction du corps final
            plain_body = "\n\n".join(paragraphs)
            
            # Ajout d'une signature professionnelle
            signature = f"\n\n--\n{from_contact['name']}\n{from_contact['position']}\n{from_contact['department']}\n{from_contact['company']}\nTél: {fake.phone_number()}"
            plain_body += signature
            
            # Version HTML du corps de l'email
            html_paragraphs = [f"<p>{p}</p>" for p in paragraphs]
            html_body = "".join(html_paragraphs)
            html_signature = f"<br><br>--<br>{from_contact['name']}<br>{from_contact['position']}<br>{from_contact['department']}<br>{from_contact['company']}<br>Tél: {fake.phone_number()}"
            html_body += html_signature
            
            # Déterminer si l'email a des pièces jointes (15% )
            has_attachments = random.random() < 0.15
            attachments = []
            
            if has_attachments:
                num_attachments = random.randint(1, 3)
                for j in range(num_attachments):
                    file_type = random.choice(list(file_extensions.keys()))
                    extension = random.choice(file_extensions[file_type])
                    
                    if file_type == "document":
                        filename = f"{fake.word()}_{fake.word()}.{extension}"
                    elif file_type == "image":
                        filename = f"IMG_{fake.numerify('######')}.{extension}"
                    elif file_type == "code":
                        filename = f"{fake.word().lower()}.{extension}"
                    elif file_type == "data":
                        filename = f"data_{fake.word().lower()}.{extension}"
                    else:
                        filename = f"archive_{fake.numerify('####')}.{extension}"
                    
                    # Taille aléatoire du fichier entre 10KB et 5MB
                    size = random.randint(10 * 1024, 5 * 1024 * 1024)
                    
                    attachments.append({
                        "id": str(uuid.uuid4()),
                        "filename": filename,
                        "mimeType": get_mime_type(extension),
                        "size": size
                    })

            if is_sent:
                # Emails envoyés
                labels = ["SENT"]
                if random.random() < 0.3:
                    labels.append("IMPORTANT")
            else:
                # Emails reçus
                num_labels = random.randint(1, 3)
                labels = ["INBOX"]
                
                if random.random() < 0.3:
                    labels.append("UNREAD")

                other_labels = [l for l in all_labels if l not in ["INBOX", "UNREAD", "SENT", "DRAFT"]]
                if other_labels:
                    additional_labels = random.sample(other_labels, min(num_labels-1, len(other_labels)))
                    labels.extend(additional_labels)
            
            # Sélection random de catégories
            num_categories = random.randint(0, 2)
            email_categories = random.sample(categories, num_categories) if random.random() > 0.3 else []
            
            # Génération de snippet
            content_start = plain_body.split('\n\n')[0] + " " + plain_body.split('\n\n')[1]
            snippet = content_start[:100] + "..." if len(content_start) > 100 else content_start
            
            # Formatage de la date selon RFC 2822
            rfc_date = email_date.strftime("%a, %d %b %Y %H:%M:%S +0000")
            iso_date = email_date.isoformat()
            
            # Création d'un ID unique pour le message
            message_id = str(uuid.uuid4())
            while message_id in all_email_ids:
                message_id = str(uuid.uuid4())
            all_email_ids.add(message_id)
            
            #  déterminer s'ils vont en CC/BCC plutôt qu'en destinataire principal
            cc_email = ""
            bcc_email = ""
            
            # Initialisation de base de l'email
            email = {
                "Message-ID": message_id,
                "Thread-ID": thread_id,
                "Labels": labels,
                "Date": rfc_date,
                "From": from_contact["email"],
                "To": to_contact["email"],
                "Cc": cc_email,
                "Bcc": bcc_email,
                "Subject": subject,
                "Body": {
                    "plain": plain_body,
                    "html": html_body
                },
                "Attachments": attachments,
                "Categories": email_categories,
                "Snippet": snippet,
                "Internal-Date": iso_date
            }

            if not is_sent and random.random() < 0.2:  # 20% des emails reçus sont en CC/BCC
                # Choisir un autre contact comme destinataire principal
                other_recipients = [c for c in contacts if c["email"] != from_contact["email"] 
                                                      and c["email"] != primary_user["email"]]
                
                if other_recipients:
                    actual_to_contact = random.choice(other_recipients)
                    
                    # Mettre l'utilisateur principal en CC (85%) ou BCC (15%)
                    if random.random() < 0.85:
                        email["To"] = actual_to_contact["email"]
                        email["Cc"] = primary_user["email"]
                    else:
                        email["To"] = actual_to_contact["email"]
                        email["Bcc"] = primary_user["email"]
                        
                    # Ajouter ce nouveau contact aux participants du thread pour cohérence future
                    if actual_to_contact not in thread_data[thread_id]['participants']:
                        thread_data[thread_id]['participants'].append(actual_to_contact)
            
            # ajouter  des destinataires en CC
            elif is_sent and random.random() < 0.3:  # 30% des emails envoyés ont des CC
                cc_candidates = [c for c in contacts if c["email"] != primary_user["email"] 
                                                   and c["email"] != to_contact["email"]]
                if cc_candidates:
                    num_cc = random.randint(1, min(3, len(cc_candidates)))
                    cc_contacts = random.sample(cc_candidates, num_cc)
                    email["Cc"] = ", ".join([c["email"] for c in cc_contacts])
                    
                    # Ajouter ces contacts aux participants du thread
                    for cc_contact in cc_contacts:
                        if cc_contact not in thread_data[thread_id]['participants']:
                            thread_data[thread_id]['participants'].append(cc_contact)
            
            # Mettre à jour les informations du thread avec cet email
            if thread_id in thread_data:
                thread_data[thread_id]['last_email'] = email
            
            emails.append(email)

        emails.sort(key=lambda x: x["Internal-Date"])
        
        # Enregistrer le lot dans le JSON
        batch_filename = os.path.join(output_dir, f"emails_batch_{batch_num + 1}.json")
        with open(batch_filename, 'w', encoding='utf-8') as f:
            json.dump(emails, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Lot {batch_num + 1} enregistré dans {batch_filename}")

        emails = None
        import gc
        gc.collect()
    
    # Créer un fichier d'index des lots
    index = {
        "total_emails": total_emails,
        "total_batches": total_batches,
        "user_email": primary_user["email"],
        "user_name": primary_user["name"],
        "batches": [f"emails_batch_{i + 1}.json" for i in range(total_batches)],
        "generation_date": datetime.now().isoformat()
    }
    
    with open(os.path.join(output_dir, "index.json"), 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2)
    
    logging.info(f"Génération terminée ! {total_emails} emails générés au total dans {total_batches} lots.")
    logging.info(f"Boîte mail générée pour {primary_user['name']} ({primary_user['email']})")
    
    return index

def get_mime_type(extension):
    mime_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "txt": "text/plain",
        "jpg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "zip": "application/zip",
        "rar": "application/x-rar-compressed",
        "py": "text/x-python",
        "js": "application/javascript",
        "html": "text/html",
        "css": "text/css",
        "json": "application/json",
        "csv": "text/csv",
        "xml": "application/xml",
        "sql": "application/sql",
        "yaml": "application/x-yaml"
    }
    return mime_types.get(extension, "application/octet-stream")

if __name__ == "__main__":
    # Générer 20 000 emails factices par lots de 5 000 pour une boîte mail personnelle
    generate_massive_dataset(40_000, 5_000, "mockdata")
