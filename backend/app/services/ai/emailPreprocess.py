import re
import codecs

def sanitize_numbers(text):
    # Replace Telephone Number or ID 
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
    # Keep Money, date
    text = re.sub(r'\$\d+\.?\d*', '[MONEY]', text)
    text = re.sub(r'\b\d{4}-\d{2}-\d{2}\b', '[DATE]', text)
    return text


def preprocess_email(text, keep_paragraphs=False):
    # 1. Handle Escape character
    text = codecs.decode(text, 'unicode_escape')
    
    # 2. Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # 3. Handle blank character
    if keep_paragraphs:
        text = re.sub(r'\n{2,}', '[PARA]', text)  # Keep paragraph seperation
        text = re.sub(r'\n', ' ', text)
    else:
        text = ' '.join(text.split())
    
    # 4. Other removals
    text = re.sub(r'[#~@$%^&*_+=}{|\]\[<>]', '', text)
    return text.strip()