from dataclasses import dataclass, field
from datetime import datetime, timezone

def _now_iso() -> str:
    """Current UTC time as a string like '2026-09-04T18:30:00+00:00'."""
    return datetime.now(timezone.utc).isoformat()

# Class for job postings information
@dataclass
class Posting:
    company: str
    title: str
    location: str
    url: str
    job_id: str
    term: str | None = None
    posted_at: str | None = None
    scraped_at: str = field(default_factory=_now_iso)
    @property
    def unique_key(self) -> str:
        return f"{self.company}:{self.job_id}"
    

    
    
if __name__ == "__main__":
    p = Posting(company="Ciena", title="SW Intern", location="Ottawa", url="https://x", job_id="R123")
    print(p)
    print("unique_key:", p.unique_key)