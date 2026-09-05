# Internship Scraping Tool

A small, self-hosted tool that watches a handful of companies' career pages for
**Summer 2027 internship / co-op postings** located in **Ottawa, Kanata, or
Canada-remote**, stores them in a local database, and **emails me only the new
ones**. Designed to run automatically and for free on **GitHub Actions**.

> This repo doubles as a learning log I'm building it to get hands-on
> experience with web scraping, databases, diffing, email automation, and CI.

## Companies tracked (starting set)

| Company | Location focus | Scrape type |
|---|---|---|
| Shopify | Ottawa | _TBD_ |
| Ciena | Kanata | Workday |
| Kinaxis | Kanata / Ottawa | _TBD_ |
| Ross Video | Ottawa | _TBD_ |
| BlackBerry / QNX | Kanata | Workday |

Adding a new company = drop one new file in `scrapers/` and register it.

## How it works

```
scrapers/*  ->  filter (location + Summer 2027)  ->  database (diff)  ->  email new postings
```

- **Static sites** are parsed from HTML with BeautifulSoup.
- **Dynamic sites** are read from their underlying JSON API (found via the
  browser Network tab) faster and more reliable than a headless browser.

## Project layout

```
.
├── scrapers/          # one file per company + a shared base class
├── models.py          # the Posting data structure
├── database.py        # SQLite storage + diffing
├── filters.py         # Ottawa/Kanata/remote + Summer 2027 matching
├── notifier.py        # Gmail email sending
├── main.py            # orchestrates a full run
├── data/              # local SQLite database lives here (git-ignored)
├── requirements.txt
└── .github/workflows/ # scheduled automation (Module 8)
```

## Setup (local development)

```bash
python -m venv venv
venv\Scripts\activate        # Windows PowerShell
pip install -r requirements.txt
cp .env.example .env         # then fill in your Gmail app password
```

## Development log

Built in modules — see commit history.

- [x] **Module 0** — Project setup (structure, git, dependencies)
- [x] **Module 1** — Data model + first scraper
- [x] **Module 2** — SQLite storage
- [x] **Module 3** — Diffing (new vs. seen)
- [x] **Module 4** — Filtering (location + term)
- [x] **Module 5** — Email notifications
- [x] **Module 6** — Remaining scrapers
- [x] **Module 7** — Config & registry
- [x] **Module 8** — GitHub Actions automation
