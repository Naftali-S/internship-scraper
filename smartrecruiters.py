"""SmartRecruiters scraper (public REST API).

    GET https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=100&offset=N

The list gives title + structured location but NOT the description, so (like
Workday) we fetch each intern's detail for the description to term-match on.
Unlocks: ServiceNow (slug 'servicenow'), Assent (slug 'assent').
"""

import time
import requests

from models import Posting
from filters import is_internship, is_target_location, mentions_term

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; internship-scraper/0.1)",
    "Accept": "application/json",
}


def scrape_smartrecruiters(company, slug):
    base = f"https://api.smartrecruiters.com/v1/companies/{slug}/postings"

    # 1) page through the list (100 per page)
    raw = []
    offset = 0
    while True:
        resp = requests.get(base, headers=HEADERS,
                            params={"limit": 100, "offset": offset}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        content = data.get("content", [])
        if not content:
            break
        raw.extend(content)
        offset += 100
        if offset >= data.get("totalFound", 0):
            break
        time.sleep(0.3)

    # 2) keep interns; fetch each one's detail for description + a clean URL
    result = []
    for job in raw:
        title = job.get("name", "")
        if not is_internship(title):
            continue

        loc = job.get("location", {})
        location = ", ".join(x for x in (loc.get("city"), loc.get("region"), loc.get("country")) if x)
        if loc.get("remote"):
            location += " (Remote)"

        if not is_target_location(location):
            continue  # skip the expensive detail fetch for non-target locations

        job_id = job.get("id", "")
        url = f"https://jobs.smartrecruiters.com/{slug}/{job_id}"
        description = ""
        try:
            d = requests.get(f"{base}/{job_id}", headers=HEADERS, timeout=30)
            if d.status_code == 200:
                dj = d.json()
                url = dj.get("applyUrl") or dj.get("postingUrl") or url
                sections = dj.get("jobAd", {}).get("sections", {})
                description = " ".join(
                    sec.get("text", "") for sec in sections.values() if isinstance(sec, dict)
                )
        except requests.RequestException:
            pass  # if detail fails, we still term-match on the title

        haystack = title + " " + description
        if mentions_term(haystack):
            result.append(Posting(
                company=company,
                title=title,
                location=location,
                url=url,
                job_id=str(job_id),
                posted_at=job.get("releasedDate"),
            ))
        time.sleep(0.3)
    return result
