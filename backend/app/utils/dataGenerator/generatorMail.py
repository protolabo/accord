import gc
import json
import random
import uuid
import base64
from datetime import datetime, timedelta
from faker import Faker
import os
from tqdm import tqdm

# Imports for the Enron data management module
from enron_data_manager import EnronDataManager  # backend/app/utils/enron_data_manager.py

# Initialize the Enron data manager with a minimum length
enron_manager = EnronDataManager('emails.json', min_body_length=150)

faker_instances = [
    Faker('en_US'),
]


def get_fake():
    return random.choice(faker_instances)


def generate_realistic_email_content(topic, fake, is_reply=False):
    """
    Generates realistic email content using real Enron data
    """
    # Try to get a real Enron email body, unused and long enough
    # with a maximum of 100 attempts
    enron_body = enron_manager.get_random_email_body(max_attempts=100)

    if enron_body:
        # Split into paragraphs and eliminate empty lines
        paragraphs = []
        for p in enron_body.split("\n\n"):
            p = p.strip()
            if p:  # Keep only non-empty paragraphs
                paragraphs.append(p)

        # If there aren't enough paragraphs, add generic content
        if len(paragraphs) < 2:
            paragraphs.extend([
                f"Regarding your request about {topic}.",
                "I will keep you informed of the next steps."
            ])

        # Limit the number of paragraphs to avoid overly long emails
        return paragraphs [:min(7, len(paragraphs))]
    else:

        return None

def get_enron_subject_for_thread(related_project, fake):
    """
    Retrieves a real Enron email subject for a new thread
    """
    enron_subject = enron_manager.get_random_email_subject()

    if enron_subject and len(enron_subject) > 4:
        return enron_subject

    # Fallback to original subject generation if no Enron subject is available
    return generate_fallback_subject(related_project, fake)


def generate_fallback_subject(related_project, fake):
    """
    Generates a fallback subject using the original method
    """
    if related_project:
        subject_templates = [
            f"{related_project['name']}: Status update",
            f"{related_project['name']} - Next steps",
            f"Action plan: {related_project['name']}",
            f"{related_project['name']} - Meeting minutes",
            f"Urgent: {related_project['name']} - Issue identified",
            f"For validation: {related_project['name']} deliverables"
        ]
        subject = random.choice(subject_templates)
    else:
        subject_templates = [
            "Information request: {topic}",
            "Invitation: {topic} meeting on {date}",
            "Follow-up: {topic}",
            "Urgent: {topic}",
            "Summary: {topic}",
            "Proposal: {topic}",
            "{topic} - For validation",
            "Update: {topic}"
        ]

        topics = [
            "Budget forecast",
            "Recruitment",
            "Quarterly planning",
            "Server migration",
            "Internal audit",
            "Marketing plan",
            "New offices",
            "Team training",
            "Technical issue",
            "Client request",
            "Quality review",
            "Internal process"
        ]

        subject = random.choice(subject_templates).format(
            topic=random.choice(topics),
            date=fake.date_this_month().strftime("%m/%d")
        )

        #print("Remember to check the subject ")
        #print(subject)

    return subject


def generate_massive_dataset(total_emails=1000,  output_dir="mock_data"):
    """
    Generates a set of email data using real Enron content

    Args:
        total_emails: Total number of emails to generate
        output_dir: Output directory
    """
    import time
    start_time = time.time()

    os.makedirs(output_dir, exist_ok=True)

    # Check if Enron data is available
    enron_available = enron_manager.is_data_available()
    if enron_available:
        print(f"Enron data successfully loaded: {enron_manager.get_email_count()} emails available")
    else:
        print("Enron data not available, using random content generation")

    # Main user
    primary_user = {
        "name": "Alexander Smith",
        "email": "alexander.smith@acmecorp.com",
        "position": "Marketing Director",
        "department": "Marketing",
        "company": "Acme Corporation"
    }

    print(f"Generating emails for {primary_user['name']}'s mailbox ({primary_user['email']})")

    companies = []
    domains = []

    # Add the user's company
    companies.append(primary_user["company"])
    domains.append("acmecorp.com")

    # Add 4 other companies
    for _ in range(4):
        fake = get_fake()
        company = fake.company()
        companies.append(company)
        domain = f"{company.lower().replace(' ', '').replace(',', '').replace('.', '')}.com"
        domains.append(domain)

    departments = [
        "Marketing", "Finance", "HR", "IT", "Sales", "Support", "Management",
        "Legal", "R&D", "Production", "Logistics", "Communications",
        "Accounting", "Customer Service", "Quality", "Purchasing"
    ]

    print("Generating professional contacts...")
    contacts = []

    # Add the main user to contacts
    contacts.append(primary_user)

    # Add 10 colleagues (same email domain as the user)
    for i in range(10):
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

    # Add 40 external contacts
    for i in range(40):
        fake = get_fake()
        company_idx = random.randint(1, len(companies) - 1)  # Exclude the main company
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

    # Create 10 fictitious projects
    projects = []
    for i in range(10):
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

    # File extension types for attachments
    file_extensions = {
        "document": ["docx", "pdf"],
        "image": ["jpg", "png"]
    }

    # Possible labels for emails
    all_labels = [
        "INBOX", "IMPORTANT", "UNREAD", "SENT", "STARRED"
    ]

    # Categories for email classification
    categories = [
        "Urgent", "Follow-up", "Project", "Administrative", "Client",
        "Supplier", "Internal", "External", "Meeting", "Training",
        "Document", "Report", "Request", "Action Required", "FYI",
        "Planning", "Budget", "Technical", "Issue", "Solution"
    ]

    # Generate threads (~ 5 emails per thread)
    thread_count = total_emails // 5
    print(f"Creating {thread_count} email threads...")

    # use list of available ID
    available_thread_ids = [str(uuid.uuid4()) for _ in range(thread_count)]
    random.shuffle(available_thread_ids)  # Mélanger pour plus d'aléatoire

    # Store threads info
    thread_data = {}  # {thread_id: {'subject': '...', 'participants': [...], 'last_email': {...}}}

    # Generate all emails at once
    all_email_ids = set()
    current_date = datetime.now()
    start_date = current_date - timedelta(days=365)  # Emails over 1 year

    print(f"Generating {total_emails} emails...")

    # Generate all emails
    emails = []
    for i in tqdm(range(total_emails)):
        fake = get_fake()

        # 40% sent emails, 60% received emails
        is_sent = random.random() < 0.4

        # 30% new threads or if no thread exists
        is_new_thread = (random.random() > 0.7 or not thread_data) and available_thread_ids

        if is_new_thread:
            # Get available ID
            thread_id = available_thread_ids.pop()
        else:
            if not thread_data:
                if available_thread_ids:
                    thread_id = available_thread_ids.pop()
                    is_new_thread = True
                else:
                    thread_id = str(uuid.uuid4())
                    is_new_thread = True
                    print(f"WARNING: Created emergency thread ID at email {i}")
            else:
                thread_candidates = list(thread_data.keys())
                thread_id = random.choice(thread_candidates)

        # Handle information for this thread
        if thread_id in thread_data:
            # Existing thread - use info for consistency
            thread_info = thread_data[thread_id]
            subject = thread_info['subject']
            # 70% chance to add RE: if not already done
            if not subject.startswith("RE: ") and random.random() > 0.3:
                subject = "RE: " + subject

            # Maintain conversation between the same participants
            participants = thread_info['participants']

            if is_sent:
                # Primary user replies
                from_contact = primary_user
                # Choose a recipient from previous participants
                to_candidates = [p for p in participants if p["email"] != primary_user["email"]]
                to_contact = random.choice(to_candidates) if to_candidates else random.choice(
                    [c for c in contacts if c["email"] != primary_user["email"]])
            else:
                # Someone replies to the primary user
                to_contact = primary_user
                # Choose a sender from previous participants
                from_candidates = [p for p in participants if p["email"] != primary_user["email"]]
                from_contact = random.choice(from_candidates) if from_candidates else random.choice(
                    [c for c in contacts if c["email"] != primary_user["email"]])

            is_reply = True
        else:
            # New thread
            is_reply = False

            # Select sender and recipient for a new thread
            if is_sent:
                from_contact = primary_user
                to_candidates = [c for c in contacts if c["email"] != primary_user["email"]]
                to_contact = random.choice(to_candidates)
            else:
                to_contact = primary_user
                from_candidates = [c for c in contacts if c["email"] != primary_user["email"]]
                from_contact = random.choice(from_candidates)

            # Select a random project (75% chance)
            related_project = random.choice(projects) if random.random() < 0.75 else None

            # Use an Enron subject for the new thread
            subject = get_enron_subject_for_thread(related_project, fake)

            thread_data[thread_id] = {
                'subject': subject,
                'participants': [from_contact, to_contact],
                'last_email': None
            }

        # Handle date - for replies, ensure they are after the last email in the thread
        if is_reply and thread_data[thread_id]['last_email']:
            last_email_date = datetime.fromisoformat(thread_data[thread_id]['last_email']['Internal-Date'])
            # Between 5 min and 24h after
            min_date = last_email_date + timedelta(minutes=random.randint(5, 1440))
            if min_date > current_date:
                min_date = last_email_date + timedelta(minutes=random.randint(5, 60))
            email_date = min_date
        else:
            # First email of a thread
            random_days = random.randint(0, 365)
            email_date = start_date + timedelta(days=random_days,
                                                hours=random.randint(0, 23),
                                                minutes=random.randint(0, 59))

        # Salutation
        salutations = [
            f"Hello {to_contact['name'].split()[0]},",
            f"Dear {to_contact['name'].split()[0]},",
            "Hello everyone,",
            "Dear colleagues,",
            f"Hi {to_contact['name'].split()[0]},",
            "Good morning,"
        ]
        opening = random.choice(salutations)

        # Message body with coherent Enron content
        content_paragraphs = generate_realistic_email_content(subject, fake, is_reply)

        # Conclusion
        closings = [
            "Regards,",
            "Best regards,",
            "Kind regards,",
            "Best wishes,",
            "Thank you,",
            "Sincerely,"
        ]
        closing = random.choice(closings)

        # Paragraph assembly
        #paragraphs = [opening] + content_paragraphs + [closing]
        paragraphs = content_paragraphs

        # Final body construction
        plain_body = "\n\n".join(paragraphs)

        # Add professional signature
        signature = f"\n\n--\n{from_contact['name']}\n{from_contact['position']}\n{from_contact['department']}\n{from_contact['company']}\nTel: {fake.phone_number()}"
        plain_body += signature

        # HTML version of the email body
        html_paragraphs = [f"<p>{p}</p>" for p in paragraphs]
        html_body = "".join(html_paragraphs)
        html_signature = f"<br><br>--<br>{from_contact['name']}<br>{from_contact['position']}<br>{from_contact['department']}<br>{from_contact['company']}<br>Tel: {fake.phone_number()}"
        html_body += html_signature

        # Determine if the email has attachments (15%)
        has_attachments = random.random() < 0.15
        attachments = []

        if has_attachments:
            num_attachments = random.randint(1, 3)
            for j in range(num_attachments):
                file_type = random.choice(list(file_extensions.keys()))
                extension = random.choice(file_extensions[file_type])

                if file_type == "document":
                    filename = f"{fake.word()}_{fake.word()}.{extension}"
                else:
                    filename = f"IMG_{fake.numerify('######')}.{extension}"

                # Random file size between 10KB and 5MB
                size = random.randint(10 * 1024, 5 * 1024 * 1024)

                attachments.append({
                    "id": str(uuid.uuid4()),
                    "filename": filename,
                    "size": size
                })

        if is_sent:
            # Sent emails
            labels = ["SENT"]
            if random.random() < 0.3:
                labels.append("IMPORTANT")
        else:
            # Received emails
            num_labels = random.randint(1, 3)
            labels = ["INBOX"]

            if random.random() < 0.3:
                labels.append("UNREAD")

            other_labels = [l for l in all_labels if l not in ["INBOX", "UNREAD", "SENT"]]
            if other_labels:
                additional_labels = random.sample(other_labels, min(num_labels - 1, len(other_labels)))
                labels.extend(additional_labels)

        # Random selection of categories
        num_categories = random.randint(0, 2)
        email_categories = random.sample(categories, num_categories) if random.random() > 0.3 else []

        # Snippet generation
        if len(plain_body.split('\n\n')) > 1:
            content_start = plain_body.split('\n\n')[0] + " " + plain_body.split('\n\n')[1]
        else:
            content_start = plain_body.split('\n\n')[0]
        snippet = content_start[:100] + "..." if len(content_start) > 100 else content_start

        # Date formatting according to RFC 2822
        rfc_date = email_date.strftime("%a, %d %b %Y %H:%M:%S +0000")
        iso_date = email_date.isoformat()

        # Creation of a unique ID for the message
        message_id = str(uuid.uuid4())
        while message_id in all_email_ids:
            message_id = str(uuid.uuid4())
        all_email_ids.add(message_id)

        # Initialize CC and BCC recipients
        cc_email = ""
        bcc_email = ""

        # Basic email initialization
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

        if not is_sent and random.random() < 0.2:  # 20% of received emails are in CC/BCC
            # Choose another contact as the main recipient
            other_recipients = [c for c in contacts if c["email"] != from_contact["email"]
                                and c["email"] != primary_user["email"]]

            if other_recipients:
                actual_to_contact = random.choice(other_recipients)

                # Put the primary user in CC (85%) or BCC (15%)
                if random.random() < 0.85:
                    email["To"] = actual_to_contact["email"]
                    email["Cc"] = primary_user["email"]
                else:
                    email["To"] = actual_to_contact["email"]
                    email["Bcc"] = primary_user["email"]

                # Add this new contact to thread participants for future coherence
                if actual_to_contact not in thread_data[thread_id]['participants']:
                    thread_data[thread_id]['participants'].append(actual_to_contact)

        # Add CC recipients
        elif is_sent and random.random() < 0.3:  # 30% of sent emails have CC
            cc_candidates = [c for c in contacts if c["email"] != primary_user["email"]
                             and c["email"] != to_contact["email"]]
            if cc_candidates:
                num_cc = random.randint(1, min(3, len(cc_candidates)))
                cc_contacts = random.sample(cc_candidates, num_cc)
                email["Cc"] = ", ".join([c["email"] for c in cc_contacts])

                # Add these contacts to thread participants
                for cc_contact in cc_contacts:
                    if cc_contact not in thread_data[thread_id]['participants']:
                        thread_data[thread_id]['participants'].append(cc_contact)

        # Update thread information with this email
        if thread_id in thread_data:
            thread_data[thread_id]['last_email'] = email

        emails.append(email)

        if i > 0 and i % 1000 == 0:
            percent_done = i / total_emails * 100
            elapsed_time = time.time() - start_time
            estimated_total = elapsed_time / (percent_done / 100)
            remaining_time = estimated_total - elapsed_time

            print(f"Progress: {i}/{total_emails} emails generated ({percent_done:.1f}%)")
            print(f"Elapsed time: {elapsed_time:.1f}s, Estimated remaining: {remaining_time:.1f}s")
            print(
                f"Thread stats: {len(thread_data)}/{thread_count} threads used, {len(available_thread_ids)} IDs available")

            # Réinitialiser le suivi des messages Enron
            enron_manager.used_message_ids.clear()

            gc.collect()

    # Sort all emails by date
    print("Sorting emails by date...")
    emails.sort(key=lambda x: x["Internal-Date"])

    # Save all emails to one file
    output_file = os.path.join(output_dir, "all_emails.json")
    print(f"Saving all emails to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(emails, f, indent=2, ensure_ascii=False)

    # Create a simpler index file
    index = {
        "total_emails": total_emails,
        "user_email": primary_user["email"],
        "user_name": primary_user["name"],
        "file": "all_emails.json",
        "generation_date": datetime.now().isoformat(),
        "data_source": "Enron dataset" if enron_available else "Synthetic data"
    }

    with open(os.path.join(output_dir, "index.json"), 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2)

    total_time = time.time() - start_time
    print(f"Generation complete in {total_time:.1f}s! {total_emails} emails generated and saved.")
    print(f"Mailbox generated for {primary_user['name']} ({primary_user['email']})")

    return index

"""
if __name__ == "__main__":
    # Generate 1000 mock emails for a personal mailbox
    generate_massive_dataset(1000,  "mockdata")
"""