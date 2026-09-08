# Internship Scraping Tool

A small, self-hosted tool that watches company career pages for **summer-term
internship / co-op postings** (roughly May–September) located in **Ottawa,
Kanata, or Canada-remote**, stores them in a local database, and **emails me
only the new ones**. It runs automatically and for free on **GitHub Actions**.

> This repo doubles as a learning log I'm building it to get hands-on
> experience with web scraping, hidden JSON APIs, databases, diffing, email
> automation, and CI.

## Companies tracked

**19 companies across 7 hiring platforms.** Each company is one row of config in
[`companies.py`](companies.py); a shared scraper handles every company on the
same platform.

| Platform | Scraper | Companies |
|---|---|---|
| Workday | [`workday.py`](workday.py) | Ciena, BlackBerry, TD, CIBC, Mitel, Accenture, BDO, PwC, Thales |
| Oracle Recruiting Cloud | [`oracle.py`](oracle.py) | Nokia, Oracle |
| Eightfold | [`eightfold.py`](eightfold.py) | Ericsson, Lockheed Martin |
| SmartRecruiters | [`smartrecruiters.py`](smartrecruiters.py) | ServiceNow, Assent |
| Ashby | [`ashby.py`](ashby.py) | Solace, Rewind |
| Lever | [`lever.py`](lever.py) | Fullscript |
| Workable | [`workable.py`](workable.py) | Nuvei |

**Adding a company on an existing platform = one line in `companies.py`.** A new
platform = one new scraper file plus a branch in `main.py`'s dispatcher.

## How it works

```
scrapers  ->  filter (location + summer term)  ->  SQLite (diff vs. seen)  ->  email only new postings
```

1. **Scrape** each company from its underlying JSON API (found via the browser
   Network tab) faster and more reliable than a headless browser. Every
   scraper filters at the source (location keyword / geo search) and caps its
   pagination so a run stays fast and bounded.
2. **Filter** for internships in the target locations and the summer term (see
   below).
3. **Diff** against the SQLite database and keep only postings never seen before.
4. **Email** the new ones as a styled HTML digest (grouped by company, with an
   apply link and where the source provides it an application deadline).

### Location filter

A posting is in scope if its location mentions **Ottawa** or **Kanata**, or is a
**Canada-remote** role.

### Summer-term filter

The goal is to catch every genuine summer-term role without hand-filtering the
inbox, so the term match is deliberately careful:

- The **title is authoritative** if it names the term ("Summer Intern",
  "May 2027"), that decides it. A title that names a *different* term ("January
  … Co-op", "Fall 2027") is dropped even if its description mentions summer
  elsewhere.
- When the title is **silent**, the **description decides** — including the
  **start date**: a May/June start reads as summer, a January/September start as
  winter/fall.
- No term anywhere → dropped.

Eightfold's search API carries no description, so for those postings the scraper
fetches the job page's schema.org **JSON-LD** to read the body and start date.

## Project layout

```
.
├── companies.py       # the registry: one dict per company, keyed by `ats`
├── main.py            # dispatches each company to its platform scraper + runs a full pass
├── models.py          # the Posting data structure
├── filters.py         # location + summer-term matching
├── database.py        # SQLite storage + diffing
├── notifier.py        # styled HTML email digest (Gmail)
├── workday.py         # per-platform scrapers ...
├── oracle.py
├── eightfold.py
├── smartrecruiters.py
├── ashby.py
├── lever.py
├── workable.py
├── data/              # local SQLite database (committed so CI runs persist state)
├── requirements.txt
└── .github/workflows/ # scheduled daily automation
```

## Setup (local development)

```bash
python -m venv venv
venv\Scripts\activate                 # Windows PowerShell
pip install -r requirements.txt
cp .env.example .env                   # then fill in EMAIL_ADDRESS / EMAIL_APP_PASSWORD / EMAIL_TO
```

Run a full pass locally:

```bash
$env:PYTHONUTF8=1; .\venv\Scripts\python.exe main.py
```

The email requires a Gmail **app password** (not your account password) in
`.env`. On GitHub Actions the same values come from repository **secrets**.

## Automation

[`.github/workflows/scrape.yml`](.github/workflows/scrape.yml) runs a full pass
on a daily cron (and on manual dispatch), then commits the updated database back
to the repo so the next run remembers what it has already emailed. Because the
cloud job writes `data/postings.db`, pull with rebase before pushing local work:

```bash
git pull --rebase && git push
```

## Development log

Built incrementally, see commit history for the full story. Highlights:

- Data model, SQLite storage, and set-based diffing
- Location + summer-term filtering, then a **high-precision** rewrite (title
  authoritative, description/start-date as the tiebreaker)
- Gmail notifications, upgraded to a **magazine-style HTML digest**
- Config-driven company registry + platform dispatcher
- Platform scrapers: Workday, Lever, Ashby, SmartRecruiters, Workable, Oracle,
  Eightfold — each with server-side prefiltering and bounded pagination
- Daily automation on GitHub Actions with database persistence
