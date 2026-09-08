import time
from concurrent.futures import ThreadPoolExecutor
import requests
from models import Posting
from filters import is_internship, is_target_location, mentions_term

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; internship-scraper/0.1)",
    "Accept": "application/json",
}

# Safety net: some tenants (e.g. Canadian banks) return their whole board for a
# broad search term, so cap how far any single search will paginate. The narrow
# "Ottawa"/"Kanata" searches finish long before this; only the broad "Remote"
# pass ever hits it, and the location prefilter discards the rest anyway.
MAX_LIST_PAGES = 10
SEARCH_TERMS = ("Ottawa", "Kanata", "Remote")

def scrape_workday(company, tenant, data_center, site):
    """Scrape on Workday careers site and return its relevant postings."""
    cxs_base = f"https://{tenant}.{data_center}.myworkdayjobs.com/wday/cxs/{tenant}/{site}"
    public_base = f"https://{tenant}.{data_center}.myworkdayjobs.com/en-US/{site}"
    
    all_postings = []
    seen = set()
    for term in SEARCH_TERMS:
        for p in _fetch_list(cxs_base, public_base, company, term):
            if p.job_id not in seen:
                seen.add(p.job_id)
                all_postings.append(p)
    interns = [p for p in all_postings if is_internship(p.title)]

    # Cheap prefilter: only interns whose LIST location already looks like a
    # target, OR is ambiguous ("N Locations" / blank, which hides the real
    # cities), are worth the expensive detail fetch.
    candidates = []
    for p in interns:
        list_loc = p.location or ""
        ambiguous = (not list_loc) or ("location" in list_loc.lower())
        if ambiguous or is_target_location(list_loc):
            candidates.append(p)

    # Detail fetches are pure network waiting, so run them concurrently instead
    # of one-at-a-time. This is what collapses the run from ~28 min to minutes.
    def enrich(p):
        try:
            location_text, description = _fetch_detail(cxs_base, public_base, p.url)
        except requests.RequestException:
            return p, ""  # one dead detail page shouldn't sink the company
        p.location = location_text
        return p, description

    result = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        for p, description in pool.map(enrich, candidates):
            # Title is authoritative for the term; the description is only a
            # fallback when the title is silent (see filters.mentions_term).
            if is_target_location(p.location) and mentions_term(p.title, description):
                result.append(p)
    return result

def _post_with_retry(url, body, retries=3):
    for attempt in range(retries):
        try: 
            response = requests.post(url, headers=HEADERS, json=body, timeout=15)
            response.raise_for_status()
            return response
        except requests.RequestException:
            if attempt == retries - 1:  # last try
                raise
            time.sleep(2 ** attempt)    # exponential wait

def _fetch_list(cxs_base, public_base, company, search_text):
    postings = []
    offset = 0
    for _ in range(MAX_LIST_PAGES):
        body = {"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": search_text}
        response = _post_with_retry(cxs_base + "/jobs", body)
        page = response.json().get("jobPostings", [])
        if not page:
            break
        for job in page:
            external_path = job.get("externalPath")
            if not external_path:
                continue
            postings.append(Posting(
                company=company,
                title=job.get("title", ""),
                location=job.get("locationsText", ""),
                url=public_base + external_path,
                job_id=external_path.rsplit("_", 1)[-1],
                posted_at=job.get("postedOn"),
            ))
        if len(page) < 20:
            break
        offset += 20
        time.sleep(0.3)
    return postings

def _get_with_retry(url, retries=2):
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            return response
        except requests.RequestException:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)

def _fetch_detail(cxs_base, public_base, url):
    external_path = url.replace(public_base, "")
    response = _get_with_retry(cxs_base + external_path)
    info = response.json().get("jobPostingInfo", {})
    locations = [info.get("location", "")] + info.get("additionalLocations", [])
    location_text = ", ".join(loc for loc in locations if loc)
    description = info.get("jobDescription",  "")
    
    return location_text, description