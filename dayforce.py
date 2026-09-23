"""Dayforce scraper (jobs.dayforcehcm.com candidate portal API).

The job search only answers with a CSRF token: get one (plus its cookie) from
/api/auth/csrf, then send both with the search. The results already include
the description and expiry date, so no per-job detail fetch is needed.
Unlocks: Ross Video (client 'rossvideo'), Payments Canada ('paymentscanada').
"""

import time

import fetch
from models import Posting
from filters import is_internship, is_target_location, mentions_term

BASE = "https://jobs.dayforcehcm.com"
MAX_LIST_PAGES = 10

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept": "application/json",
}


def scrape_dayforce(company, client, board="CANDIDATEPORTAL"):
    csrf = fetch.get(f"{BASE}/api/auth/csrf", headers=HEADERS)
    headers = {**HEADERS, "X-CSRF-TOKEN": csrf.json().get("csrfToken", "")}

    result = []
    for job in _fetch_list(client, board, headers, csrf.cookies):
        title = job.get("jobTitle", "")
        if not is_internship(title):
            continue

        location = "; ".join(loc.get("formattedAddress", "") for loc in job.get("postingLocations", []))
        if job.get("hasVirtualLocation"):
            location += " (Remote)"

        description = job.get("jobDescription", "") or ""
        if is_target_location(location) and mentions_term(title, description):
            job_id = str(job.get("jobPostingId", ""))
            result.append(Posting(
                company=company,
                title=title,
                location=location,
                url=f"{BASE}/en-US/{client}/{board}/jobs/{job_id}",
                job_id=job_id,
                posted_at=job.get("postingStartTimestampUTC"),
                deadline=job.get("postingExpiryTimestampUTC"),  # None for most postings; that's fine
            ))
    return result


def _fetch_list(client, board, headers, cookies):
    postings = []
    start = 0
    for _ in range(MAX_LIST_PAGES):
        body = {"clientNamespace": client, "jobBoardCode": board, "cultureCode": "en-US",
                "distanceUnit": 0, "paginationStart": start}
        response = fetch.post(f"{BASE}/api/geo/{client}/jobposting/search",
                              json=body, headers=headers, cookies=cookies)
        data = response.json()
        page = data.get("jobPostings", [])
        if not page:
            break
        postings.extend(page)
        start += len(page)
        if start >= data.get("maxCount", 0):
            break
        time.sleep(0.3)
    return postings
