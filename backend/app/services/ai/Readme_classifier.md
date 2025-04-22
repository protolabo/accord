Use function process_email(raw_email: dict) -> dict in backend/app/servieces/ai/pipeline to do the classification

The input is a raw email data in dict form, make sure it has the "body" and "subject" keys to execute
raw_email.get("body", "") and raw_email.get("subject", "")

The output is a dict with main_class and sub_class with confidence score
ex. {
        "main_class": ["Bills","Notifications"],
        "sub_classes": [["Tax Notices",0.23519957065582275],
                        ["Credit Card Payments",0.23116543889045715]]
    }

Can be test within the file (just comment out), the data used for test is stocked in data folder under mock_emails.json
