import re

INTERN_KEYWORDS = ["intern", "co-op", "coop", "student"]
# Words that contain "intern" but aren't internships ("Director, International
# Relations"). They're removed from the title before the keyword check.
INTERN_LOOKALIKES = ["international", "internal", "internet"]
LOCATION_KEYWORDS = ["ottawa", "kanata"]
# "canada (remote)" is how the scrapers that add a " (Remote)" suffix write a
# Canada-wide remote job (Workable, BambooHR, Dayforce), e.g. Fidus Systems.
REMOTE_CANADA_KEYWORDS = ["remote-canada", "remote - canada", "canada remote", "remote, canada", "canada (remote)"]

# --- UK and Ireland ---
# A country word anywhere in the location is enough ("Glasgow, Scotland",
# "Ampthill, GBR", "UK-Wimborne", "Dublin 2, Ireland").
UK_IE_COUNTRY_WORDS = {"uk", "gb", "gbr", "england", "scotland", "wales", "britain", "ireland", "ie", "irl"}
UK_IE_COUNTRY_PHRASES = ["united kingdom", "great britain", "northern ireland", "republic of ireland"]

# A city name alone ("London", "London (Remote)") only counts when nothing
# Canadian or American is in the same location. London, Cambridge, Windsor,
# Dublin, Manchester and Bristol all exist in Canada or the US too
# ("London, Ontario", "London (ON), ON, CA", "US-CT-New London", "Dublin, OH").
UK_IE_CITIES = [
    "london", "manchester", "birmingham", "leeds", "glasgow", "edinburgh", "bristol",
    "cardiff", "belfast", "newcastle", "liverpool", "sheffield", "nottingham", "leicester",
    "derby", "reading", "cambridge", "oxford", "southampton", "coventry", "milton keynes",
    "brighton", "crawley", "stevenage", "guildford", "warwick", "swindon", "chester",
    "knutsford", "northampton", "bournemouth", "telford", "aberdeen", "dundee", "bath",
    "york", "slough", "staines", "sunbury", "weybridge", "macclesfield", "basingstoke",
    "farnborough", "farringdon", "canary wharf", "gatwick", "filton",
    "dublin", "cork", "galway", "limerick", "waterford", "athlone", "kilkenny",
]
NORTH_AMERICA_WORDS = {
    "canada", "ontario", "on", "ca", "quebec", "qc", "alberta", "ab", "bc", "manitoba",
    "toronto", "montreal", "vancouver", "calgary", "edmonton", "winnipeg", "halifax",
    "mississauga", "waterloo", "kitchener", "saskatoon", "regina", "burnaby", "markham",
    "usa", "us", "america",
    # US state abbreviations; "in", "or", "me", "hi", "ok", "de" and "id" are left out
    # because they are also ordinary words
    "al", "ak", "az", "ar", "co", "ct", "fl", "ga", "ia", "il", "ks", "ky", "la", "ma",
    "md", "mi", "mn", "mo", "ms", "mt", "nc", "nd", "ne", "nh", "nj", "nm", "nv", "ny",
    "oh", "pa", "ri", "sc", "sd", "tn", "tx", "ut", "va", "vt", "wa", "wi", "wv", "wy",
}
# Full US state names catch "Cambridge, Massachusetts"; "new york" stops York matching.
NORTH_AMERICA_PHRASES = [
    "united states", "new london", "new york", "new jersey", "new hampshire",
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut",
    "delaware", "florida", "georgia", "hawaii", "idaho", "illinois", "indiana", "iowa",
    "kansas", "kentucky", "louisiana", "maine", "maryland", "massachusetts", "michigan",
    "minnesota", "mississippi", "missouri", "montana", "nebraska", "nevada", "new mexico",
    "north carolina", "north dakota", "ohio", "oklahoma", "oregon", "pennsylvania",
    "rhode island", "south carolina", "south dakota", "tennessee", "texas", "utah",
    "vermont", "virginia", "washington", "wisconsin", "wyoming",
    "british columbia", "nova scotia", "new brunswick", "saskatchewan", "newfoundland",
]
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
# absent (e.g. "Start date: May 4th, 2027"). Winter/Fall start months are
# already handled by OTHER_TERM_KEYWORDS (january, september, ...).
#
# How the pattern reads, left to right (text is already lowercased):
#   start\w*            "start" plus any letters after it: start, starts, starting
#   [^.\n]{0,20}        up to 20 characters that aren't a period or line break,
#                       so the date has to be in the same sentence: " date: "
#   \b(?:may|june)\b    the whole word "may" or "june" (\b = word boundary, so
#                       "mayor" or "dismay" don't count)
#   [.,\s]+\d           then spaces/punctuation and a digit: " 4", ", 2027"
#
# Why each part is there:
#   - the digit at the end separates the month from the verb "may"
#     ("you may be required" has no number after it)
#   - "start" at the front skips unrelated May dates ("apply by May 1")
#   - the same-sentence window stops a "start" in one sentence from pairing
#     with a "May" somewhere else
#
# Matches:        "start date: may 4th, 2027", "starting june 1, 2027",
#                 "anticipated start: may 2027"
# Doesn't match:  "you may start soon", "apply by may 1",
#                 "start date: january 4, 2027"
_SUMMER_START = re.compile(r"start\w*[^.\n]{0,20}\b(?:may|june)\b[.,\s]+\d")


# --- Year of study ---
# Bump both every cycle. Postings that only take students graduating before
# GRADUATION_YEAR are dropped (most UK internships are "penultimate year" only,
# which for a 2029 graduate means the summer 2028 cycle, not 2027).
INTERNSHIP_YEAR = 2027
GRADUATION_YEAR = 2029
# "Graduating in 2027", "expected graduation between Dec 2027 and Jun 2028",
# "class of 2028". The window after the phrase is scanned for years.
_GRAD_PHRASE = re.compile(r"\b(?:graduating|graduation|graduate in|graduate by|class of)\b(.{0,60})")
_YEAR = re.compile(r"\b20\d\d\b")
# Placements longer than a summer don't fit May to August.
LONG_PLACEMENT_KEYWORDS = [
    "placement year", "industrial placement", "year in industry", "year-long", "year long",
    "6 month", "6-month", "8 month", "8-month", "12 month", "12-month", "13 month", "13-month",
    "16 month", "16-month",
]


def _year_eligible(text):
    """False when the posting is limited to students graduating before GRADUATION_YEAR."""
    penultimate_ok = GRADUATION_YEAR == INTERNSHIP_YEAR + 1
    if "penultimate" in text and not penultimate_ok:
        return False
    years = [int(y) for window in _GRAD_PHRASE.findall(text) for y in _YEAR.findall(window)]
    if years and max(years) < GRADUATION_YEAR:
        return False
    return True


def _is_summer(text):
    return any(k in text for k in TERM_KEYWORDS) or bool(_SUMMER_START.search(text))

def is_internship(title):
    text = title.lower()
    for word in INTERN_LOOKALIKES:
        text = text.replace(word, "")
    return any(keyword in text for keyword in INTERN_KEYWORDS)

def is_target_location(location):
    loc = (location or "").lower()
    if any(keyword in loc for keyword in LOCATION_KEYWORDS):
        return True
    if any(keyword in loc for keyword in REMOTE_CANADA_KEYWORDS):
        return True
    return is_uk_ie_location(loc)

def is_uk_ie_location(location):
    loc = (location or "").lower()
    words = set(re.findall(r"[a-z]+", loc))
    if words & UK_IE_COUNTRY_WORDS or any(p in loc for p in UK_IE_COUNTRY_PHRASES):
        return True
    if words & NORTH_AMERICA_WORDS or any(p in loc for p in NORTH_AMERICA_PHRASES):
        return False
    return any(re.search(rf"\b{city}\b", loc) for city in UK_IE_CITIES)

def mentions_term(title, description=""):
    """Decide whether a posting is a summer role this student can apply to.

    Two checks: the role is open to his year of study (see _year_eligible) and
    isn't a long placement, and it is a SUMMER-term role (_summer_term).
    """
    t = title.lower()
    d = (description or "").lower()
    if any(k in t for k in LONG_PLACEMENT_KEYWORDS):
        return False
    if not _year_eligible(t + " " + d):
        return False
    return _summer_term(t, d)


def _summer_term(t, d):
    """Decide whether a posting is a SUMMER-term role.

    The title is authoritative when it names a term; the description is only a
    tiebreaker when the title is silent. This avoids the false positive where a
    Jan/Sept posting's body enumerates every term the employer offers, while
    still catching untermed-title co-ops whose term lives in the description.
    """
    if _is_summer(t):
        return True                       # title explicitly says summer
    if any(k in t for k in OTHER_TERM_KEYWORDS):
        return False                      # title explicitly says another term
    if _is_summer(d):                     # title silent -> description decides
        return True                       # summer word or a May/June start date
    if any(k in d for k in OTHER_TERM_KEYWORDS):
        return False                      # winter/fall word or start month
    return False                          # no term stated anywhere -> drop