import fetch
from models import Posting
from filters import is_internship, is_target_location, mentions_term

def scrape_lever(company, slug):
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    response = fetch.get(url, timeout=30)
    jobs = response.json()  #a list of posting discts

    result = []
    for job in jobs:
        title = job.get("text", "")
        if not is_internship(title):
            continue
        location = job.get("categories", {}).get("location", "") or ""
        description = job.get("descriptionPlain", "") or ""
        if is_target_location(location) and mentions_term(title, description):
            result.append(Posting(
                company=company,
                title=title,
                location=location,
                url=job.get("hostedUrl", ""),
                job_id=str(job.get("id", "")),
            ))
    return result
