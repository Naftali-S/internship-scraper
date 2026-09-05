import time
import requests
from models import Posting

DETAIL_BASE = "https://ciena.wd5.myworkdayjobs.com/wday/cxs/ciena/Careers"
PUBLIC_BASE = "https://ciena.wd5.myworkdayjobs.com/en-US/Careers"


def fetch_ciena_detail(url):
    """Given a posting's public URL, return (full_location_text, description)."""
    external_path = url.replace(PUBLIC_BASE, "")    #turn the public URL back into the API path
    headers = {"User-Agent": "Mozilla/5.0 (compatible; internship-scraper/0.1)",
               "Accept": "application/json"}
    response = requests.get(DETAIL_BASE + external_path, headers=headers, timeout=30)
    response.raise_for_status()
    info = response.json().get("jobPostingInfo", {})
    
    locations = [info.get("location", "")] + info.get("additionalLocations", [])
    location_text = ", ".join(loc for loc in locations if loc)
    description = info.get("jobDescription", "")
    return location_text, description

def fetch_ciena() -> list[Posting]:
    url = "https://ciena.wd5.myworkdayjobs.com/wday/cxs/ciena/Careers/jobs"
    # appears as user
    headers = {"User-Agent": "Mozilla/5.0(compatible; internship-scraper/0.1)"}
    postings = [] # collect posting objects
    offset = 0 # start at first page
    while True:
        body = {"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": ""}
        response = requests.post(url, headers=headers, json=body, timeout=30)
        response.raise_for_status()
        data = response.json()

        page = data.get("jobPostings", [])
        if not page:
            break
        for job in page:
            external_path = job["externalPath"]
            job_id = external_path.rsplit("_", 1)[-1] # splits on the last underscore and takes the piece after it
            job_url = "https://ciena.wd5.myworkdayjobs.com/en-US/Careers" + external_path
            postings.append(Posting(
                company="Ciena",
                title=job["title"],
                location=job.get("locationsText", ""),
                url=job_url,
                job_id=job_id,
                posted_at=job.get("postedOn"),
                ))
        if len(page) < 20:
            break          # a not-full page = the last page
        offset += 20       # move to the next page
        time.sleep(0.3)    # be polite
    return postings

if __name__ == "__main__":
    results = fetch_ciena()
    print(f"Fetched {len(results)} postings. First 5:")
    for p in results[:5]:
        print(f" - {p.title} | {p.location} | {p.job_id}")
    
    
    
    
    
    
    
                
    
