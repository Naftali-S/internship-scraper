import requests
from models import Posting
from filters import is_internship, is_target_location, mentions_term

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; internship-scraper/0.1)",
    "Accept": "application/json"}

def scrape_lever(company, slug):
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    jobs = response.json()  #a list of posting discts
    
    result = []
    for job in jobs:
        title = job.get("text", "")
        if not is_internship(title):
            continue
        location = job.get("categories", {}).get("location", "") or ""
        description = job.get("descriptionPlain", "") or ""
        haystack = title + " " + description
        if is_target_location(location) and mentions_term(haystack):
            result.append(Posting(
                company=company,
                title=title,
                location=location,
                url=job.get("hostedUrl", ""),
                job_id=str(job.get("id", "")),
            ))
    return result