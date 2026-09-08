"""Eightfold scraper (public PCSX search API).

    GET https://{host}/api/pcsx/search
        ?domain={domain}&location=Ottawa, Canada&start=N&num=10

Positions are under data.positions[] with `name` (title), `locations`
(granular, e.g. "Ottawa,Ontario,Canada"), `positionUrl` (relative), and
`postedTs` (epoch seconds). There is no description in the list, so we
term-match on the title (consistent with the other scrapers).

The `location` query narrows server-side (Ericsson 510 -> 13) and its geo
radius covers the Ottawa metro incl. Kanata; we still re-check
is_target_location for precision. `num` is capped at 10 by the API, so we page
with `start`. No application deadline is provided. Unlocks: Ericsson, Lockheed.
"""

import time
from datetime import datetime, timezone
import requests

from models import Posting
from filters import is_internship, is_target_location, mentions_term

PAGE_SIZE = 10                       # the API caps `num` at 10
MAX_LIST_PAGES = 20                  # safety net against a runaway loop
LOCATION_QUERY = "Ottawa, Canada"    # geo search; radius covers Kanata too


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
        if not mentions_term(title):
            continue

        path = pos.get("positionUrl", "") or ""
        url = path if path.startswith("http") else f"https://{host}{path}"
        result.append(Posting(
            company=company,
            title=title,
            location=location,
            url=url,
            job_id=job_id,
            posted_at=_epoch_to_date(pos.get("postedTs")),
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


def _epoch_to_date(ts):
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).date().isoformat()
    except (ValueError, OSError, TypeError):
        return None
