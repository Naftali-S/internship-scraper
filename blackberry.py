from workday import scrape_workday

def get_blackberry_postings():
    return scrape_workday("BlackBerry",  tenant="bb", data_center="wd3", site="BlackBerry")