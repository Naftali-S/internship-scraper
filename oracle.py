"""Oracle Recruiting Cloud scraper (public candidate-experience REST API).

The list response already contains the description text AND the application
deadline (PostingEndDate), so no per-job detail fetch is needed.

We use Oracle's own server-side `keyword` search as the LOCATION filter (city
keywords), because the returned PrimaryLocation is often only country-level
("Canada") with the real city buried in the description. Trusting the keyword
search avoids wrongly rejecting those. Unlocks: Oracle, Nokia.
"""

import fetch
from models import Posting
from filters import is_internship, is_target_location, mentions_term

# Server-side location filter (Oracle keyword search). Narrow city terms keep
# each query tiny, so a small page cap is plenty of headroom. Canadian results
# trust the keyword (PrimaryLocation is often only "Canada"); UK results are
# re-checked, because "London" also finds London, Ontario.
LOCATION_KEYWORDS = {
    "ca": ("Ottawa", "Kanata"),
    "uk": ("London", "Manchester", "Edinburgh", "Dublin", "United Kingdom"),
}
PAGE_SIZE = 100
MAX_LIST_PAGES = 5


def scrape_oracle(company, pod, site, regions=("ca",)):
    base = f"https://{pod}/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
    job_base = f"https://{pod}/hcmUI/CandidateExperience/en/sites/{site}/job"

    result = []
    seen = set()
    for region, keyword in [(r, k) for r in regions for k in LOCATION_KEYWORDS[r]]:
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
            if region != "ca" and not is_target_location(location):
                continue

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
        response = fetch.get(url, timeout=30)
        items = response.json().get("items", [])
        page = items[0].get("requisitionList", []) if items else []
        if not page:
            break
        reqs.extend(page)
        if len(page) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return reqs
