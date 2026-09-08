"""Oracle Recruiting Cloud scraper (public candidate-experience REST API).

    GET https://{pod}/hcmRestApi/resources/latest/recruitingCEJobRequisitions
        ?onlyData=true
        &expand=requisitionList.secondaryLocations,flexFieldsFacet.values
        &finder=findReqs;keyword=<kw>,siteNumber=<site>,limit=<n>,offset=<n>,sortBy=POSTING_DATES_DESC

The list response already contains the description text AND the application
deadline (PostingEndDate), so no per-job detail fetch is needed.

We use Oracle's own server-side `keyword` search as the LOCATION filter (city
keywords), because the returned PrimaryLocation is often only country-level
("Canada") with the real city buried in the description. Trusting the keyword
search avoids wrongly rejecting those. Unlocks: Oracle, Nokia.
"""

import requests
from models import Posting
from filters import is_internship, mentions_term

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; internship-scraper/0.1)",
    "Accept": "application/json",
}

# Server-side location filter (Oracle keyword search). Narrow city terms keep
# each query tiny, so a small page cap is plenty of headroom.
LOCATION_KEYWORDS = ("Ottawa", "Kanata")
PAGE_SIZE = 100
MAX_LIST_PAGES = 5


def scrape_oracle(company, pod, site):
    base = f"https://{pod}/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
    job_base = f"https://{pod}/hcmUI/CandidateExperience/en/sites/{site}/job"

    result = []
    seen = set()
    for keyword in LOCATION_KEYWORDS:
        for req in _fetch_reqs(base, site, keyword):
            job_id = str(req.get("Id", ""))
            if not job_id or job_id in seen:
                continue
            seen.add(job_id)

            title = req.get("Title", "") or ""
            if not is_internship(title):
                continue

            # Title is authoritative; fall back to the list's description fields
            # when the title doesn't name a term (see filters.mentions_term).
            description = " ".join(str(req.get(f, "") or "") for f in
                                   ("ShortDescriptionStr", "ExternalQualificationsStr",
                                    "ExternalResponsibilitiesStr"))
            if not mentions_term(title, description):
                continue

            secondary = ", ".join(
                s.get("Name", "") for s in (req.get("secondaryLocations") or []) if s.get("Name")
            )
            location = req.get("PrimaryLocation", "") or ""
            if secondary:
                location = f"{location}, {secondary}" if location else secondary

            result.append(Posting(
                company=company,
                title=title,
                location=location,
                url=f"{job_base}/{job_id}",
                job_id=job_id,
                posted_at=req.get("PostedDate"),
                deadline=req.get("PostingEndDate"),  # None for many tenants; that's fine
            ))
    return result


def _fetch_reqs(base, site, keyword):
    reqs = []
    offset = 0
    for _ in range(MAX_LIST_PAGES):
        finder = (f"findReqs;keyword={keyword},siteNumber={site},"
                  f"limit={PAGE_SIZE},offset={offset},sortBy=POSTING_DATES_DESC")
        url = (f"{base}?onlyData=true"
               f"&expand=requisitionList.secondaryLocations,flexFieldsFacet.values"
               f"&finder={finder}")
        response = _get_with_retry(url)
        items = response.json().get("items", [])
        page = items[0].get("requisitionList", []) if items else []
        if not page:
            break
        reqs.extend(page)
        if len(page) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return reqs


def _get_with_retry(url, retries=2):
    import time
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            return response
        except requests.RequestException:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
