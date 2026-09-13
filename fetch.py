import time
import requests

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; internship-scraper/0.1)",
    "Accept": "application/json",
}
            
def request(method, url, *, retries=3, timeout=20, headers=None, **kwargs):
    headers = headers or DEFAULT_HEADERS
    for attempt in range(retries):
        try:
            response = requests.request(method, url, headers=headers, timeout=timeout, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException:
            if attempt == retries - 1:   # last try: let the caller see the failure
                raise
            time.sleep(2 ** attempt)

def get(url, **kwargs):
    return request("GET", url, **kwargs)

def post(url, **kwargs):
    return request("POST", url, **kwargs)
            