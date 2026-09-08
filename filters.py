import re

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

# If a TITLE (or, when the title is silent, the DESCRIPTION) names one of these,
# the role is some other term — not summer.
OTHER_TERM_KEYWORDS = [
    "winter", "fall", "autumn", "spring",
    "january", "february", "september", "october", "november", "december",
]

# A May/June START date implies a summer term even when the word "summer" is
# absent (e.g. "Start date: May 4th, 2027"). The trailing digit distinguishes
# the month from the verb "may" ("may be required"), and anchoring to "start"
# avoids matching an unrelated May deadline. Winter/Fall start months are
# already handled by OTHER_TERM_KEYWORDS (january, september, ...).
_SUMMER_START = re.compile(r"start\w*[^.\n]{0,20}\b(?:may|june)\b[.,\s]+\d")


def _is_summer(text):
    return any(k in text for k in TERM_KEYWORDS) or bool(_SUMMER_START.search(text))

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

def mentions_term(title, description=""):
    """Decide whether a posting is a SUMMER-term role.

    The title is authoritative when it names a term; the description is only a
    tiebreaker when the title is silent. This avoids the false positive where a
    Jan/Sept posting's body enumerates every term the employer offers, while
    still catching untermed-title co-ops whose term lives in the description.
    """
    t = title.lower()
    if _is_summer(t):
        return True                       # title explicitly says summer
    if any(k in t for k in OTHER_TERM_KEYWORDS):
        return False                      # title explicitly says another term
    d = (description or "").lower()        # title silent -> description decides
    if _is_summer(d):
        return True                       # summer word or a May/June start date
    if any(k in d for k in OTHER_TERM_KEYWORDS):
        return False                      # winter/fall word or start month
    return False                          # no term stated anywhere -> drop