import time
import requests
from models import Posting
from filters import is_internship, is_target_location, mentions_term

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; internship-scraper/0.1)",
    "Accept": "application/json",
}

def scrape_workday(company, tenant, data_center, site):
    """Scrape on Workday careers site and return its relevant postings."""
    cxs_base = f"https://{tenant}.{data_center}.myworkdayjobs.com/wday/cxs/{tenant}/{site}"
    public_base = f"https://{tenant}.{data_center}.myworkdayjobs.com/en-US/{site}"
    
    all_postings = _fetch_list(cxs_base, public_base, company)
    interns = [p for p in all_postings if is_internship(p.title)]
    
    result = []
    for p in interns:
        location_text, description = _fetch_detail(cxs_base, public_base, p.url)
        p.location = location_text
        haystack = p.title + " " + description
        if is_target_location(location_text) and mentions_term(haystack):
            result.append(p)
        time.sleep(0.3)  
    return result

def _fetch_list(cxs_base, public_base, company):
    postings = []
    offset = 0
    while True:
        body = {"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": ""}
        response = requests.post(cxs_base + "/jobs", headers=HEADERS, json=body, timeout=30)
        response.raise_for_status()
        page = response.json().get("jobPostings", [])
        if not page:
            break
        for job in page:
            external_path = job["externalPath"]
            postings.append(Posting(
                company=company,
                title=job["title"],
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

def _fetch_detail(cxs_base, public_base, url):
    external_path = url.replace(public_base, "")
    response = requests.get(cxs_base + external_path, headers=HEADERS, timeout=30)
    response.raise_for_status()
    info = response.json().get("jobPostingInfo", {})
    locations = [info.get("location", "")] + info.get("additionalLocations", [])
    location_text = ", ".join(loc for loc in locations if loc)
    description = info.get("jobDescription",  "")
    
    return location_text, description