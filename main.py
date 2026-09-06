from companies import COMPANIES 
from workday import scrape_workday
from lever import scrape_lever
from database import get_connection, init_db, get_existing_keys, save_postings
from notifier import send_digest

def scrape_company(company):
    """Route a company entry to the right platform scraper."""
    ats = company["ats"]
    if ats == "workday":
        return scrape_workday(company["name"], company["tenant"], company["dc"], company["site"])
    # future: elif ats == "greenhouse": return scrape_greenhouse(...)
    if ats == "lever":
        return scrape_lever(company["name"], company["slug"])
    raise ValueError(f"Unknown ATS '{ats}' for {company['name']}")
    
def run():
    conn = get_connection()
    init_db(conn)
    
    postings = []
    for company in COMPANIES:
        try:
            postings.extend(scrape_company(company)) #run each company's scraper and collect results
        except Exception as e:
            print(f"  ! {company['name']} failed: {e}") #one bad company won't kill the run
        
    existing = get_existing_keys(conn)    #what's been seen before
    new = [p for p in postings if p.unique_key not in existing] #keep each posting on if key isn't already existing
    
    send_digest(new)                #send email
    save_postings(conn, new)        #remember the new ones
    
    print(f"Scanned {len(COMPANIES)} companies, kept {len(postings)} relevant, {len(new)} new")
    for p in new[:20]:
        print(f"  NEW: {p.company} | {p.title} | {p.location}")

if __name__ == "__main__":
    run()