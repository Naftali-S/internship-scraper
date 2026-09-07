import os
import smtplib
import html
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
    
def format_html(postings):
    cards = ""
    for p in postings:
        title = html.escape(p.title)
        company = html.escape(p.company)
        location = html.escape(p.location)
        posted = html.escape(p.posted_at or "")
        cards += f"""
        <div style="border:1px solid #e6e6e6;border-radius:10px;padding:16px;margin-bottom:12px;">
          <a href="{p.url}" style="font-size:16px;font-weight:600;color:#1a73e8;text-decoration:none;">{title}</a>
          <div style="color:#555;font-size:14px;margin-top:6px;">
            <strong>{company}</strong> &middot; {location}
          </div>
          <div style="color:#999;font-size:12px;margin-top:4px;">{posted}</div>
        </div>
        """
    return f"""
    <div style="font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;max-width:600px;margin:0 auto;padding:16px;background:#ffffff;">
      <h2 style="color:#202124;margin-bottom:4px;">🎓 {len(postings)} new internship posting(s)</h2>
      <p style="color:#777;font-size:13px;margin-top:0;">Ottawa / Kanata / Canada-remote · Summer 2027</p>
      {cards}
      <p style="color:#bbb;font-size:11px;margin-top:24px;">Sent automatically by your internship scraper.</p>
    </div>
    """