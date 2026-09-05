import os
import smtplib
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
    msg.set_content(format_body(postings))
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        server.send_message(msg)
    
    print(f"Emailed {len(postings)} posting(s) to {EMAIL_TO}")