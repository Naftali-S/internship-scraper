import time
import requests
from models import Posting

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
            job_id = external_path.rsplit("_", 1)[-1]
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
    
    
    
    
    
    
    
                
    
