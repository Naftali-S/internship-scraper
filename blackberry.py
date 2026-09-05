import time
import requests
from models import Posting
from filters import is_internship, is_target_location, mentions_term

DETAIL_BASE = "https://bb.wd3.myworkdayjobs.com/wday/cxs/bb/BlackBerry"
PUBLIC_BASE = "https://bb.wd3.myworkdayjobs.com/en-US/BlackBerry"


def fetch_blackberry_detail(url):
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

def fetch_blackberry() -> list[Posting]:
    url = "https://bb.wd3.myworkdayjobs.com/wday/cxs/bb/BlackBerry/jobs"
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
            job_url = PUBLIC_BASE + external_path
            postings.append(Posting(
                company="BlackBerry",
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

def get_blackberry_postings():
    all_postings = fetch_blackberry()
    interns = [p for p in all_postings if is_internship(p.title)]
    result = []
    for p in interns:
        location_text, description = fetch_blackberry_detail(p.url)
        p.location = location_text
        haystack = p.title + " " + description
        if is_target_location(location_text) and mentions_term(haystack):
            result.append(p)
        time.sleep(0.3)
    return result

if __name__ == "__main__":
    results = fetch_blackberry()
    print(f"Fetched {len(results)} postings. First 5:")
    for p in results[:5]:
        print(f" - {p.title} | {p.location} | {p.job_id}")
    
    
    
    
    
    
    
                
    
