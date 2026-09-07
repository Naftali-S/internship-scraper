import os
import smtplib
import html
from datetime import datetime
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv() # reads .env into environment variables

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
EMAIL_TO = os.getenv("EMAIL_TO")

def format_body(postings):
    lines = [f"{len(postings)} new internship posting(s):", ""]
    for p in postings:
        lines.append(f"- {p.title}")
        lines.append(f"  {p.location}")
        lines.append(f"  {p.url}")
        lines.append("")
    return "\n".join(lines)

def send_digest(postings):
    if not postings:
        print("No new postings. Skipping email")
        return
    
    msg = EmailMessage()
    msg["Subject"] = f"[Internships] {len(postings)} new posting(s)"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_TO
    msg.set_content(format_body(postings))  # fallback
    msg.add_alternative(format_html(postings), subtype="html")   # the pretty version
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        server.send_message(msg)
    
    print(f"Emailed {len(postings)} posting(s) to {EMAIL_TO}")
    
def _pretty_date(value):
    """ISO timestamp -> 'Sep 07, 2026'. Non-ISO strings pass through unchanged."""
    if not value:
        return ""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%b %d, %Y")
    except (ValueError, AttributeError):
        return value


def _posting_card(p):
    """One job as a magazine-style card (email-safe inline styles)."""
    title = html.escape(p.title)
    location = html.escape(p.location or "")
    url = html.escape(p.url or "", quote=True)
    posted = _pretty_date(p.posted_at)
    deadline = getattr(p, "deadline", None)  # deadline-ready; shows only if present

    meta = f'<div style="font-size:13px;color:#5b6472;margin:2px 0;">&#128205; {location}</div>' if location else ""
    posted_row = f'<div style="font-size:12px;color:#9aa1ac;margin:2px 0;">Posted {html.escape(posted)}</div>' if posted else ""
    deadline_row = (
        f'<div style="display:inline-block;font-size:12px;font-weight:600;color:#b23b3b;'
        f'background:#fdecec;border-radius:6px;padding:3px 9px;margin-top:8px;">&#9203; Apply by {html.escape(str(deadline))}</div>'
        if deadline else ""
    )
    return f"""
        <div style="background:#ffffff;border:1px solid #e6e8ec;border-radius:12px;padding:18px 20px;margin:0 0 14px 0;">
          <a href="{url}" style="display:block;font-size:16px;font-weight:600;line-height:1.35;color:#16213e;text-decoration:none;margin:0 0 6px 0;">{title}</a>
          {meta}
          {posted_row}
          {deadline_row}
          <div style="margin-top:14px;">
            <a href="{url}" style="display:inline-block;background:#2557d6;color:#ffffff;font-size:13px;font-weight:600;text-decoration:none;padding:9px 18px;border-radius:8px;">Apply &rarr;</a>
          </div>
        </div>"""


def format_html(postings):
    # Group by company, preserving the order companies first appear.
    groups = {}
    for p in postings:
        groups.setdefault(p.company, []).append(p)

    sections = ""
    for company, items in groups.items():
        cards = "".join(_posting_card(p) for p in items)
        sections += f"""
        <div style="margin:30px 0 16px 0;border-bottom:2px solid #16213e;padding-bottom:8px;">
          <div style="font-size:20px;font-weight:700;color:#16213e;letter-spacing:-0.01em;">{html.escape(company)}</div>
        </div>
        {cards}"""

    stats = f"{len(postings)} new posting{'s' if len(postings) != 1 else ''} &middot; {len(groups)} compan{'ies' if len(groups) != 1 else 'y'} &middot; {datetime.now().strftime('%b %d, %Y')}"

    body = f"""
    <div style="background:#f4f5f7;padding:24px 12px;font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
      <div style="max-width:640px;margin:0 auto;">
        <div style="background:#16213e;border-radius:14px;padding:28px 24px;margin:0 0 8px 0;">
          <div style="font-size:22px;font-weight:700;color:#ffffff;letter-spacing:-0.01em;">&#127891; Internship Digest</div>
          <div style="font-size:13px;color:#aab3c5;margin-top:6px;">Ottawa &middot; Kanata &middot; Canada-remote &mdash; Summer 2027</div>
          <div style="font-size:13px;color:#8b97b0;margin-top:16px;">{stats}</div>
        </div>
        {sections}
        <div style="text-align:center;color:#aab3c5;font-size:11px;margin-top:28px;">Sent automatically by your internship scraper</div>
      </div>
    </div>
    """
    # Full document + color-scheme lock: tells clients that honor it (e.g. Apple
    # Mail) not to auto-invert into dark mode. Gmail keeps our explicit colors
    # anyway; Outlook.com may still force-invert (not controllable).
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<meta name="supported-color-schemes" content="light">
</head>
<body style="margin:0;padding:0;background:#f4f5f7;">
{body}
</body>
</html>"""