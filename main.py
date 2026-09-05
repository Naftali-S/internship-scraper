from ciena import fetch_ciena
from database import get_connection, init_db, get_existing_keys, save_postings


def run():
    conn = get_connection()
    init_db(conn)
    
    postings = fetch_ciena()        #fetch everything
    existing = get_existing_keys(conn)    #what's been seen before
    new = [p for p in postings if p.unique_key not in existing] #keep each posting on if key isn't already existing
    
    save_postings(conn, new)        #remember the new ones
    
    print(f"Fetched {len(postings)}, {len(new)} new this run")
    for p in new[:10]:
        print(f"  NEW: {p.title} | {p.location}")

if __name__ == "__main__":
    run()