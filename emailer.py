import smtplib
import ssl
import time
import json
import os
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "sent_history.json")

def load_sent_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_sent_history(history):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"[Error saving history] {e}")

def verify_smtp_connection(smtp_host, smtp_port, username, password, use_tls=True):
    """
    Test if SMTP credentials work properly.
    """
    try:
        port = int(smtp_port)
        if port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_host, port, context=context, timeout=10) as server:
                server.login(username, password)
        else:
            with smtplib.SMTP(smtp_host, port, timeout=10) as server:
                if use_tls:
                    server.starttls(context=ssl.create_default_context())
                server.login(username, password)
        return True, "SMTP connection and authentication successful!"
    except Exception as e:
        return False, f"SMTP Connection failed: {str(e)}"

def render_template(template_str, lead_data):
    """
    Replaces variables like {business_name}, {website}, {email}, {niche}, {location}
    """
    rendered = template_str
    for key, value in lead_data.items():
        rendered = rendered.replace(f"{{{key}}}", str(value or ""))
    return rendered

def send_single_email(smtp_config, to_email, subject, body_text, body_html=None):
    """
    Sends one email through configured SMTP.
    """
    smtp_host = smtp_config.get("host")
    smtp_port = int(smtp_config.get("port", 587))
    username = smtp_config.get("username")
    password = smtp_config.get("password")
    from_name = smtp_config.get("from_name", "")
    from_email = smtp_config.get("from_email", username)
    
    msg = MIMEMultipart("alternative")
    sender_header = f"{from_name} <{from_email}>" if from_name else from_email
    msg["From"] = sender_header
    msg["To"] = to_email
    msg["Subject"] = subject
    
    # Attach plain text
    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    
    # Attach HTML if provided
    if body_html:
        msg.attach(MIMEText(body_html, "html", "utf-8"))
        
    if smtp_port == 465:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context, timeout=15) as server:
            server.login(username, password)
            server.sendmail(from_email, [to_email], msg.as_string())
    else:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.starttls(context=ssl.create_default_context())
            server.login(username, password)
            server.sendmail(from_email, [to_email], msg.as_string())
            
    return True

def run_campaign(leads, smtp_config, subject_template, body_template, 
                 delay_range=(30, 60), status_callback=None, stop_event=None):
    """
    Iterates over leads, renders templates, sends with throttling, and updates history.
    """
    history = load_sent_history()
    total = len(leads)
    sent_count = 0
    skipped_count = 0
    failed_count = 0
    
    def log(msg, item=None):
        if status_callback:
            status_callback({'message': msg, 'item': item, 'sent': sent_count, 'total': total})
        print(f"[Campaign] {msg}")

    log(f"Starting campaign for {total} leads...")

    for idx, lead in enumerate(leads):
        if stop_event and stop_event.is_set():
            log("Campaign stopped by user.")
            break
            
        email = lead.get("email")
        if not email:
            continue
            
        # Check duplicate
        if email.lower() in history:
            skipped_count += 1
            log(f"Skipping already emailed lead: {email}")
            continue
            
        # Render template
        subject = render_template(subject_template, lead)
        body = render_template(body_template, lead)
        
        log(f"Sending ({idx + 1}/{total}) to {lead.get('business_name')} <{email}>...")
        try:
            send_single_email(smtp_config, email, subject, body)
            sent_count += 1
            history[email.lower()] = {
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                'business_name': lead.get('business_name'),
                'subject': subject
            }
            save_sent_history(history)
            log(f"✓ Sent successfully to {email}")
            
            # Throttle delay (unless last email)
            if idx < total - 1:
                wait_secs = random.uniform(delay_range[0], delay_range[1])
                log(f"Sleeping {wait_secs:.1f}s for spam-filter protection...")
                # Sleep in increments to allow fast cancellation
                slept = 0
                while slept < wait_secs:
                    if stop_event and stop_event.is_set():
                        break
                    time.sleep(1)
                    slept += 1
        except Exception as e:
            failed_count += 1
            log(f"✗ Failed to send to {email}: {str(e)}")
            
    log(f"Campaign complete: {sent_count} sent, {skipped_count} skipped, {failed_count} failed.")
    return {
        'sent': sent_count,
        'skipped': skipped_count,
        'failed': failed_count
    }
