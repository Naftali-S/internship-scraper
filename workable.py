"""Workable scraper (public account widget API).

    GET https://www.workable.com/api/accounts/{account_id}?details=true

Returns a `jobs` array with title, structured location, url, and (with
details=true) a description. Unlocks: Nuvei (account_id '378737').
"""

import requests

from models import Posting
from filters import is_internship, is_target_location, mentions_term

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; internship-scraper/0.1)",
    "Accept": "application/json",
}


def scrape_workable(company, account_id):
    url = f"https://www.workable.com/api/accounts/{account_id}?details=true"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    jobs = resp.json().get("jobs", [])

    result = []
    for job in jobs:
        title = job.get("title", "")
        if not is_internship(title):
            continue

        loc = job.get("location", {}) or {}
        location = ", ".join(x for x in (loc.get("city"), loc.get("region"), loc.get("country")) if x)
        if loc.get("telecommuting"):
            location += " (Remote)"

        description = job.get("description", "") or ""
        if is_target_location(location) and mentions_term(title, description):
            result.append(Posting(
                company=company,
                title=title,
                location=location,
                url=job.get("url", "") or job.get("application_url", ""),
                job_id=str(job.get("id") or job.get("shortcode", "")),
                posted_at=job.get("published_on") or job.get("created_at"),
            ))
    return result
