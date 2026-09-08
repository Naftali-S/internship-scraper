import requests
from models import Posting
from filters import is_internship, is_target_location, mentions_term

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; internship-scraper/0.1)",
           "Accept": "application/json"}


def scrape_ashby(company, slug):
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=false"
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    jobs = response.json().get("jobs", [])

    result = []
    for job in jobs:
        title = job.get("title", "")
        if not is_internship(title):
            continue

        # combine primary + any secondary locations into one string
        parts = [job.get("location", "")]
        for s in job.get("secondaryLocations", []):
            parts.append(s if isinstance(s, str) else s.get("location", ""))
        location = ", ".join(p for p in parts if p)

        description = job.get("descriptionPlain", "") or ""
        if is_target_location(location) and mentions_term(title, description):
            result.append(Posting(
                company=company,
                title=title,
                location=location,
                url=job.get("jobUrl", ""),
                job_id=str(job.get("id", "")),
                posted_at=job.get("publishedAt"),
            ))
    return result