"""Jibe scraper (the careers site many iCIMS companies use, e.g. careers.kpmg.ca).

The search is already narrowed to Ottawa server-side and each job carries its
full description, so no per-job detail fetch is needed. Unlocks: KPMG.
"""

import time

import fetch
from models import Posting
from filters import is_internship, is_target_location, mentions_term

LOCATION = "Ottawa"          # distance search, so it covers Kanata too
PAGE_SIZE = 10
MAX_LIST_PAGES = 15


def scrape_jibe(company, host):
    result = []
    for job in _fetch_list(host):
        title = job.get("title", "")
        if not is_internship(title):
            continue

        location = job.get("full_location", "") or ""   # every city a multi-location job is open in
        description = " ".join(str(job.get(f, "") or "") for f in
                               ("description", "qualifications", "responsibilities"))
        if is_target_location(location) and mentions_term(title, description):
            result.append(Posting(
                company=company,
                title=title,
                location=location,
                url=f"https://{host}/jobs/{job.get('slug')}?lang=en-us",
                job_id=str(job.get("req_id", "")),
                posted_at=job.get("posted_date"),
            ))
    return result


def _fetch_list(host):
    jobs = []
    for page in range(1, MAX_LIST_PAGES + 1):
        response = fetch.get(f"https://{host}/api/jobs", params={"location": LOCATION, "page": page})
        batch = response.json().get("jobs", [])
        if not batch:
            break
        jobs.extend(j.get("data", {}) for j in batch)
        if len(batch) < PAGE_SIZE:
            break
        time.sleep(0.3)
    return jobs
