# Breakage-detection thresholds.
# A drop to zero only alerts when a company was RELIABLY producing postings
# recently, so ordinary off-season zeros never fire. A thrown error always
# alerts (that can never be confused with "no postings").
MIN_HISTORY = 3      # need at least this many recent ok-runs before a zero can flag
WINDOW = 5           # how many recent ok-runs the baseline looks at
MIN_POSITIVE = 3     # of those, how many must be > 0 to call the company "reliable"

# Known gap (future upgrade): a scraper whose API silently changes shape but
# still returns HTTP 200 returns 0 without throwing. Off-season its baseline is
# also 0, so this stays (correctly) quiet. Catching that year-round needs raw
# pre-filter counts per scraper; deferred by choice.


def evaluate(outcomes, baselines):
    """Return a list of flags (empty = all healthy)."""
    flags = []
    for name, postings, status, error in outcomes:
        if status == "error":
            flags.append(f"{name} errored: {error}")
            continue
        if len(postings) == 0:
            counts = baselines.get(name, [])
            positive = [c for c in counts if c > 0]
            if len(counts) >= MIN_HISTORY and len(positive) >= MIN_POSITIVE:
                flags.append(f"{name} returned 0 (recent runs had up to {max(counts)})")
    return flags