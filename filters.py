INTERN_KEYWORDS = ["intern", "co-op", "coop", "student"]
LOCATION_KEYWORDS = ["ottawa", "kanata"]
REMOTE_CANADA_KEYWORDS = ["remote-canada", "remote - canada", "canada remote", "remote, canada"]
TERM_KEYWORDS = ["summer 2027", "2027 summer", "may 2027"]

def is_internship(title):
    text = title.lower()
    return any(keyword in text for keyword in INTERN_KEYWORDS)

def is_target_location(location):
    loc = location.lower()
    if any(keyword in loc for keyword in LOCATION_KEYWORDS):
        return True
    if any(keyword in loc for keyword in REMOTE_CANADA_KEYWORDS):
        return True
    return False

def filter_postings(postings):
    return [
        p for p in postings
        if is_internship(p.title) and is_target_location(p.location)
    ]

def mentions_term(text):
    return any(keyword in text.lower() for keyword in TERM_KEYWORDS)  