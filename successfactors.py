"""SAP SuccessFactors scraper (Career Site Builder sites, e.g. jobs.scotiabank.com).

There's no usable JSON API (the RSS feed stops at 20 jobs), so we read the
search results page. The list gives title, location, and date but NOT the
description, so (like Workday) we fetch each target intern's job page for it.
Unlocks: Scotiabank, EY, Leonardo DRS, SAP.
"""

import time
import requests

import fetch
from models import Posting
from filters import is_internship, is_target_location, mentions_term

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept": "text/html",
}

# Some sites match the location exactly instead of by distance (Leonardo DRS
# finds nothing for "Ottawa" but lists its Kanata jobs), so search both.
SEARCH_TERMS = ("intern", "internship", "co-op", "student")
LOCATIONS = ("Ottawa", "Kanata")
PAGE_SIZE = 25
MAX_LIST_PAGES = 4


def scrape_successfactors(company, host):
    base = f"https://{host}"

    all_postings = []
    seen = set()
    for term in SEARCH_TERMS:
        for location in LOCATIONS:
            for p in _fetch_list(base, company, term, location):
                if p.job_id not in seen:
                    seen.add(p.job_id)
                    all_postings.append(p)

    result = []
    for p in all_postings:
        if not (is_internship(p.title) and is_target_location(p.location)):
            continue  # skip the job page fetch for non-interns / non-target locations
        description = ""
        try:
            description = _fetch_description(p.url)
        except requests.RequestException:
            pass  # if the job page fails, we still term-match on the title
        if mentions_term(p.title, description):
            result.append(p)
        time.sleep(0.3)
    return result


def _fetch_list(base, company, term, location):
    postings = []
    start = 0
    for _ in range(MAX_LIST_PAGES):
        params = {"q": term, "locationsearch": location, "startrow": start}
        response = fetch.get(base + "/search/", params=params, headers=HEADERS)
        rows = response.text.split('<tr class="data-row">')[1:]
        for row in rows:
            href = row.split('href="', 1)[1].split('"', 1)[0]
            posted_at = None
            if 'class="jobDate' in row:   # not every site shows a date column (EY doesn't)
                posted_at = row.split('class="jobDate', 1)[1].split(">", 1)[1].split("<", 1)[0].strip()
            postings.append(Posting(
                company=company,
                title=row.split('class="jobTitle-link">', 1)[1].split("</a>", 1)[0].strip(),
                location=row.split('class="jobLocation">', 1)[1].split("<", 1)[0].strip(),
                url=base + href,
                job_id=href.rstrip("/").rsplit("/", 1)[-1],
                posted_at=posted_at,
            ))
        if len(rows) < PAGE_SIZE:
            break
        start += PAGE_SIZE
        time.sleep(0.3)
    return postings


def _fetch_description(url):
    page = fetch.get(url, headers=HEADERS).text
    if 'class="jobdescription">' not in page:
        return ""
    body = page.split('class="jobdescription">', 1)[1]
    return body.split("</span>\n    </span>", 1)[0]   # the description's closing tags
