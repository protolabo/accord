import re

def normalize_email(email, cache=None):
    """
    Normalize an email address for consistent comparison.

    Args:
        email: Email address to normalize
        cache: Optional cache dictionary for performance

    Returns:
        Normalized email address
    """
    if not email:
        return ""

    # Check cache first if provided
    if cache is not None and email in cache:
        return cache[email]

    # Extract email from "Name <email@domain>" format
    if '<' in email and '>' in email:
        try:
            email = re.search(r'<([^>]+)>', email).group(1)
        except (AttributeError, IndexError):
            print(f"Could not parse email address: {email}")
            return None

    normalized = email.lower().strip()

    # Store in cache if provided
    if cache is not None:
        cache[email] = normalized

    return normalized


def extract_email_parts(email):
    """
    Extract domain, name, etc. from an email address.

    Args:
        email: Email address

    Returns:
        Tuple of (email, domain, name)
    """
    if not email:
        return None, None, None

    # Extract domain
    try:
        domain_match = re.search(r'@([^@]+)$', email)
        domain = domain_match.group(1) if domain_match else None
    except (AttributeError, IndexError):
        domain = None

    # Extract username
    try:
        name_match = re.search(r'^([^@]+)@', email)
        username = name_match.group(1) if name_match else None
    except (AttributeError, IndexError):
        username = None

    # Build name from username
    # to improve for example remove the numbers in the address
    parts = username.split('.') if username else []
    name = ' '.join([p.capitalize() for p in parts if p]) if parts else None

    return email, domain, name