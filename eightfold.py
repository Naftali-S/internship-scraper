"""Eightfold scraper (public PCSX search API).

Positions are under data.positions[] with `name` (title), `locations`
(granular, e.g. "Ottawa,Ontario,Canada"), `positionUrl` (relative), and
`postedTs` (epoch seconds). The search list has no description, so for each
target-location intern we fetch the job page's schema.org JobPosting JSON-LD
for the body (the term / start date lives there) and the validThrough apply-by
date.

The `location` query narrows server-side (Ericsson 510 -> 13) and its geo
radius covers the Ottawa metro incl. Kanata; we still re-check
is_target_location for precision. `num` is capped at 10 by the API, so we page
with `start`. Unlocks: Ericsson, Lockheed.
"""

import time
import json
import re
from datetime import datetime, timezone
import requests

from models import Posting
from filters import is_internship, is_target_location, mentions_term

PAGE_SIZE = 10                       # the API caps `num` at 10
MAX_LIST_PAGES = 20                  # safety net against a runaway loop
LOCATION_QUERY = "Ottawa, Canada"    # geo search; radius covers Kanata too

# The search API returns no description, but each job page embeds a schema.org
# JobPosting as JSON-LD (stable, standardised) with the full body + validThrough
# (apply-by) date. We parse that for the term filter.
_JSONLD_RE = re.compile(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>',
                        re.DOTALL | re.IGNORECASE)
_TAG_RE = re.compile(r'<[^>]+>')


def scrape_eightfold(company, host, domain):
    base = f"https://{host}/api/pcsx/search"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; internship-scraper/0.1)",
        "Accept": "application/json",
        "Referer": f"https://{host}/careers",
    }

    result = []
    seen = set()
    for pos in _fetch_positions(base, domain, headers):
        job_id = str(pos.get("displayJobId") or pos.get("id") or "")
        if not job_id or job_id in seen:
            continue
        seen.add(job_id)

        title = pos.get("name", "") or ""
        if not is_internship(title):
            continue

        location = ", ".join(pos.get("locations") or [])
        if not is_target_location(location):
            continue

        path = pos.get("positionUrl", "") or ""
        url = path if path.startswith("http") else f"https://{host}{path}"

        # Fetch the job page's JSON-LD for the description (the term / start date
        # lives there) and the apply-by date. Only the few target-location
        # interns reach here, so this stays cheap.
        posting = _fetch_jobposting(url, headers)
        if not mentions_term(title, posting.get("description", "")):
            continue

        result.append(Posting(
            company=company,
            title=title,
            location=location,
            url=url,
            job_id=job_id,
            posted_at=_epoch_to_date(pos.get("postedTs")),
            deadline=posting.get("deadline"),
        ))
    return result


def _fetch_positions(base, domain, headers):
    positions = []
    start = 0
    for _ in range(MAX_LIST_PAGES):
        params = {"domain": domain, "location": LOCATION_QUERY,
                  "start": start, "num": PAGE_SIZE}
        response = _get_with_retry(base, params, headers)
        data = response.json().get("data", {})
        page = data.get("positions", [])
        if not page:
            break
        positions.extend(page)
        start += PAGE_SIZE
        if start >= (data.get("count") or 0):
            break
        time.sleep(0.3)
    return positions


def _get_with_retry(url, params, headers, retries=2):
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            return response
        except requests.RequestException:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)


def _fetch_jobposting(url, headers):
    """Pull the schema.org JobPosting JSON-LD off a job page.

    Returns {'description': <plain text>, 'deadline': 'YYYY-MM-DD' | None}, or an
    empty dict if the page or its JSON-LD can't be read (the caller then falls
    back to a title-only term match).
    """
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.RequestException:
        return {}
    for block in _JSONLD_RE.findall(response.text):
        try:
            data = json.loads(block)
        except ValueError:
            continue
        for item in (data if isinstance(data, list) else [data]):
            if isinstance(item, dict) and item.get("@type") == "JobPosting":
                description = _TAG_RE.sub(" ", item.get("description", "") or "")
                valid_through = item.get("validThrough")
                deadline = str(valid_through).split("T", 1)[0] if valid_through else None
                return {"description": description, "deadline": deadline}
    return {}


def _epoch_to_date(ts):
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).date().isoformat()
    except (ValueError, OSError, TypeError):
        return None
