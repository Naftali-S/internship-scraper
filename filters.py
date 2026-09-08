INTERN_KEYWORDS = ["intern", "co-op", "coop", "student"]
LOCATION_KEYWORDS = ["ottawa", "kanata"]
REMOTE_CANADA_KEYWORDS = ["remote-canada", "remote - canada", "canada remote", "remote, canada"]
# Target the SUMMER term (roughly May–September) for the upcoming cycle.
# "summer" is the core signal and catches "Summer Intern", "Summer 2027",
# "Winter or Summer 2027", etc. The month-range phrasings catch summer roles
# that state start/end dates instead of the season name. Year is intentionally
# not hard-checked: live postings target the upcoming summer, and the season
# word avoids going stale each year (no need to bump "2027" -> "2028").
TERM_KEYWORDS = [
    "summer",
    "may to august", "may to september",
    "may - august", "may - september",
    "may-aug", "may-sep",
]
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