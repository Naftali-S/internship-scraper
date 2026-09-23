"""BambooHR scraper (public careers JSON).

The list gives title + location but NOT the description, so (like
SmartRecruiters) we fetch each intern's detail to term-match on.
Unlocks: Giatec, CIRA, Enghouse.
"""

import requests

import fetch
from models import Posting
from filters import is_internship, is_target_location, mentions_term

# BambooHR turns away non-browser User-Agents.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept": "application/json",
}


def scrape_bamboohr(company, subdomain):
    base = f"https://{subdomain}.bamboohr.com/careers"
    resp = fetch.get(f"{base}/list", headers=HEADERS)
    jobs = resp.json().get("result", [])

    result = []
    for job in jobs:
        title = job.get("jobOpeningName", "")
        if not is_internship(title):
            continue

        loc = job.get("location", {}) or {}
        if not loc.get("city"):
            loc = job.get("atsLocation", {}) or {}   # some boards fill this one instead
        location = ", ".join(x for x in (loc.get("city"), loc.get("state") or loc.get("province"), loc.get("country")) if x)
        if job.get("isRemote"):
            location += " (Remote)"

        if not is_target_location(location):
            continue  # skip the detail fetch for non-target locations

        job_id = job.get("id", "")
        url = f"{base}/{job_id}"
        description = ""
        posted_at = None
        try:
            d = fetch.get(f"{base}/{job_id}/detail", headers=HEADERS)
            opening = d.json().get("result", {}).get("jobOpening", {})
            description = opening.get("description", "") or ""
            posted_at = opening.get("datePosted")
            url = opening.get("jobOpeningShareUrl") or url
        except requests.RequestException:
            pass  # if detail fails, we still term-match on the title

        if mentions_term(title, description):
            result.append(Posting(
                company=company,
                title=title,
                location=location,
                url=url,
                job_id=str(job_id),
                posted_at=posted_at,
            ))
    return result
