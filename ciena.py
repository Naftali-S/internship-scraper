from workday import scrape_workday

def get_ciena_postings():
    return scrape_workday("Ciena", tenant="ciena", data_center="wd5", site="Careers")