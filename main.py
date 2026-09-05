import time
from ciena import fetch_ciena, fetch_ciena_detail
from database import get_connection, init_db, get_existing_keys, save_postings
from filters import is_internship, is_target_location, mentions_term
from notifier import send_digest
def run():
    conn = get_connection()
    init_db(conn)
    
    all_postings = fetch_ciena()        #fetch everything
    interns = [p for p in all_postings if is_internship(p.title)]
    
    postings = []
    for p in interns:
        location_text, description = fetch_ciena_detail(p.url)
        p.location = location_text
        haystack = p.title + " " + description
        if is_target_location(location_text) and mentions_term(haystack):
            postings.append(p)
        time.sleep(0.3)
    existing = get_existing_keys(conn)    #what's been seen before
    new = [p for p in postings if p.unique_key not in existing] #keep each posting on if key isn't already existing
    
    send_digest(new)                #send email
    save_postings(conn, new)        #remember the new ones
    
    print(f"Fetched {len(postings)}, {len(new)} new this run")
    for p in new[:10]:
        print(f"  NEW: {p.title} | {p.location}")

if __name__ == "__main__":
    run()