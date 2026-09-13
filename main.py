from concurrent.futures import ThreadPoolExecutor
from companies import COMPANIES 
from workday import scrape_workday
from lever import scrape_lever
from ashby import scrape_ashby
from smartrecruiters import scrape_smartrecruiters
from workable import scrape_workable
from oracle import scrape_oracle
from eightfold import scrape_eightfold
from database import get_connection, init_db, get_existing_keys, save_postings, record_runs, recent_counts
from notifier import send_digest
import health

def scrape_company(company):
    """Route a company entry to the right platform scraper."""
    ats = company["ats"]
    if ats == "workday":
        return scrape_workday(company["name"], company["tenant"], company["dc"], company["site"])
    # future: elif ats == "greenhouse": return scrape_greenhouse(...)
    if ats == "lever":
        return scrape_lever(company["name"], company["slug"])
    if ats == "ashby":
        return scrape_ashby(company["name"], company["slug"])
    if ats == "smartrecruiters":
        return scrape_smartrecruiters(company["name"], company["slug"])
    if ats == "workable":
        return scrape_workable(company["name"], company["account_id"])
    if ats == "oracle":
        return scrape_oracle(company["name"], company["pod"], company["site"])
    if ats == "eightfold":
        return scrape_eightfold(company["name"], company["host"], company["domain"])
    raise ValueError(f"Unknown ATS '{ats}' for {company['name']}")

def _scrape_safe(company):
    name = company["name"]
    try:
        postings = scrape_company(company)
        return (name, postings, "ok", None)
    except Exception as e:
        print(f" ! {name} failed: {e}")
        return (name, [], "error", str(e))
    
def run():
    conn = get_connection()
    init_db(conn)

    with ThreadPoolExecutor(max_workers=6) as pool:
        outcomes = list(pool.map(_scrape_safe, COMPANIES))

    postings = []
    for name, company_postings, status, error in outcomes:
        postings.extend(company_postings)

    # Read each company's baseline BEFORE recording this run, so the baseline
    # reflects prior runs only, then flag, then record this run.
    baselines = {name: recent_counts(conn, name, limit=health.WINDOW)
                 for name, _, _, _ in outcomes}
    flags = health.evaluate(outcomes, baselines)
    record_runs(conn, outcomes)

    existing = get_existing_keys(conn)
    new = [p for p in postings if p.unique_key not in existing]

    send_digest(new, flags)
    save_postings(conn, new)

    print(f"Scanned {len(COMPANIES)} companies, kept {len(postings)} relevant, {len(new)} new")
    for f in flags:
        print(f"  HEALTH: {f}")
    for p in new[:20]:
        print(f"  NEW: {p.company} | {p.title} | {p.location}")

if __name__ == "__main__":
    run()