from sentence_transformers import SentenceTransformer, util
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer('paraphrase-mpnet-base-v2')


category_descriptions = {
    "Project Communication": "Discussions related to specific projects, including progress updates, task assignments, risk alerts, and resource coordination. Typically contains project names, milestones, deliverables, and attachments like requirements documents.",
    "Meeting Scheduling": "Invitations or updates for meetings, containing time/location, agenda, participant list, and conference links (Zoom/Teams). May include rescheduling or cancellation notices.",
    "Task Assignment": "Clear instructions assigning responsibilities with deadlines, priority levels, and expected deliverables. Often references task tracking tools like JIRA or Trello.",
    "Client Communication": "External communications with clients or partners, covering contract negotiations, requirements confirmation, service agreements, or issue resolution.",
    "Internal Announcements": "Company-wide policy updates, organizational changes, HR notifications, or department-wide announcements requiring employee acknowledgment.",
    "Job Applications": "Emails related to hiring processes, including interview scheduling, offer letters, resume submissions, or recruitment campaign notifications.",
    "File Collaboration": "Sharing documents via cloud storage links (Google Drive, OneDrive) or collaborative editing requests, often with version control and access permissions.",

    "Social Invitation": "Invitations to social events (parties, weddings, gatherings) containing event type, date, location, dress code, or RSVP requests. May include digital invites or calendar attachments.",
    "Receipt & Tracking": "Purchase confirmations, order receipts, payment invoices, and shipping/delivery updates. Typically includes order numbers, tracking IDs, retailer names, and estimated arrival dates.",
    "Personal Health": "Appointment reminders (doctor, dentist), medical test results, prescription refill notices, or wellness program updates from healthcare providers.",
    "Personal Activity Announcement": "Notifications about personal hobbies, course enrollments (e.g., yoga classes), event participation confirmations, or local community activity bulletins.",
    "Family": "Direct communications with family members regarding personal matters, family event coordination, childcare updates, or shared household documents like schedules or budgets.",

    "Bank Statements": "Monthly or quarterly bank account summaries showing transactions, balances, service fees, or overdraft alerts. Includes account numbers and PDF statements.",
    "Credit Card Payments": "Credit card bills with due dates, minimum payment amounts, transaction details, and reward point summaries. May include fraud alerts or spending limit notices.",
    "Utilities & Rent": "Recurring bills for electricity, water, gas, internet, or rent payments. Contains service periods, usage metrics (e.g., kWh), and payment deadlines.",
    "Loans & Mortgages": "Installment payment reminders for personal loans, home mortgages, or car loans. Details principal/interest breakdowns and remaining balances.",
    "Insurance Premiums": "Payments for health, auto, or property insurance policies. Includes policy numbers, coverage periods, and claim-related updates.",
    "Investment Reports": "Statements for stocks, bonds, or mutual funds showing dividends, capital gains, portfolio performance, or tax documents (e.g., 1099 forms).",
    "Subscription Services": "Auto-renewal notices for streaming (Netflix/Spotify), software subscriptions (Adobe), or membership fees (gym, clubs).",
    "Tax Notices": "Tax payment deadlines, IRS/GOV filings (e.g., VAT), refund statuses, or audit notifications from government agencies.",

    "Promotions & Discounts": "Commercial offers with limited-time discounts, coupon codes, or flash sales from retailers/brands. Includes price comparisons, holiday deals (e.g., Black Friday), and abandoned cart reminders.",
    "Paid Subscriptions": "Renewal notices for paid services (streaming, software licenses, membership tiers) with payment amounts, renewal dates, and cancellation policies. Excludes free trials.",
    "Event & Activity Ads": "Promotions for webinars, conferences, workshops, or local events requiring registration. May offer early-bird pricing or limited seats.",
    "Newsletters": "Curated content subscriptions (industry news, blogs, educational content) with embedded article links and unsubscribe options. Typically non-transactional.",
    "Membership Exclusives": "Special offers for loyalty program members (e.g., Amazon Prime, airline status). Mentions membership tiers or reward redemptions.",
    "Free Trial Reminders": "Notifications about upcoming free trial expirations (e.g., 'Your 30-day trial ends in 3 days'). Includes upgrade prompts.",
    "Unwanted Subscriptions": "Low-priority or spammy ads (e.g., gambling, adult content), newsletters from unsubscribed sources, or duplicate promotions.",

    "Assignment": "Course-related tasks requiring submission, including deadlines, grading rubrics, or feedback from instructors. May reference platforms like Moodle or Blackboard.",
    "Education Notification": "Official announcements from educational institutions, such as semester schedules, exam date changes, campus closures, or scholarship opportunities.",
    "Education Renewals": "Reminders for course enrollment extensions, library membership renewals, or subscription-based learning platform (e.g., Coursera) payment updates.",

    "Contract": "Legally binding agreements (employment, service, NDA) requiring signatures, with clauses, effective dates, and termination terms. Often PDF attachments.",
    "Report": "Formatted analytical outputs like project reviews, financial summaries, or research findings. Includes charts, data tables, and version histories.",
    "Personal Info": "Sensitive documents for identity verification (passport scans), password resets, or official records (birth certificates).",

    "Appointment": "Confirmations or changes to scheduled appointments (medical, academic advising, vehicle maintenance) with time/location adjustments.",
    "Account Notification": "Security alerts (login attempts), account expiration warnings, or service suspensions from banks, emails, or SaaS platforms.",
    "Social Media Notices": "Platform-specific alerts from Facebook, Twitter/X, or LinkedIn, including login verifications, post interactions, or policy updates."

}

# Encoder les Decriptions des classes
category_names = list(category_descriptions.keys())
category_texts = [f"{name}: {desc}" for name, desc in category_descriptions.items()]
category_embeddings = model.encode(category_texts)

# Fonction de classification
def classify_email(email_text, threshold=0.2):
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
# sample_email = "Traveling to have a business meeting takes the fun out of the trip.  Especially if you have to prepare a presentation.  I would suggest holding the business plan meetings here then take a trip without any formal business meetings.  I would even try and get some honest opinions on whether a trip is even desired or necessary.\n\nAs far as the business meetings, I think it would be more productive to try and stimulate discussions across the different groups about what is working and what is not.  Too often the presenter speaks and the others are quiet just waiting for their turn.   The meetings might be better if held in a round table discussion format.  \n\nMy suggestion for where to go is Austin.  Play golf and rent a ski boat and jet ski's.  Flying somewhere takes too much time."
sample_email = "Here are the documents"
predicted_class, confidence = classify_email(sample_email)
print(f"Predicted: {predicted_class} (Confidence: {confidence:.2f})")
