from ciena import get_ciena_postings
from blackberry import get_blackberry_postings
from database import get_connection, init_db, get_existing_keys, save_postings
from notifier import send_digest

SCRAPERS = [get_ciena_postings, get_blackberry_postings]

def run():
    conn = get_connection()
    init_db(conn)
    
    postings = []
    for scrape in SCRAPERS:
        postings.extend(scrape()) #run each company's scraper and collect results
        
    existing = get_existing_keys(conn)    #what's been seen before
    new = [p for p in postings if p.unique_key not in existing] #keep each posting on if key isn't already existing
    
    send_digest(new)                #send email
    save_postings(conn, new)        #remember the new ones
    
    print(f"Kept {len(postings)} relevant, {len(new)} new this run")
    for p in new[:10]:
        print(f"  NEW: {p.company} | {p.title} | {p.location}")

if __name__ == "__main__":
    run()