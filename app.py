import os
import csv
import json
import io
import uuid
import threading
import time
from flask import Flask, render_template, request, jsonify, Response, send_file, session
from scraper import find_leads
from job_scraper import find_jobs_and_hr
from emailer import verify_smtp_connection, run_campaign, load_sent_history, send_single_email
from career_engine import (
    DEFAULT_CANDIDATE, 
    generate_tailored_resume, 
    generate_tailored_cover_letter, 
    generate_tailored_cold_emails
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(32))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "user_data")
os.makedirs(DATA_DIR, exist_ok=True)
LOGS_MAX = 100

def get_session_id():
    if 'sid' not in session:
        session['sid'] = str(uuid.uuid4())
    return session['sid']

def user_dir(sid):
    d = os.path.join(DATA_DIR, sid)
    os.makedirs(d, exist_ok=True)
    return d

# Global runtime state — per-session keyed dict
_sessions = {}
_sessions_lock = threading.Lock()

def get_state(sid):
    with _sessions_lock:
        if sid not in _sessions:
            _sessions[sid] = {
                'scraper': {'running': False, 'logs': [], 'current_count': 0, 'target_count': 0, 'stop_event': None, 'thread': None},
                'job_scraper': {'running': False, 'logs': [], 'current_count': 0, 'target_count': 0, 'stop_event': None, 'thread': None},
                'campaign': {'running': False, 'logs': [], 'sent': 0, 'total': 0, 'stop_event': None, 'thread': None},
            }
        return _sessions[sid]

# --- SESSION-SCOPED PERSISTENCE HELPERS ---
def load_leads(sid=None):
    path = os.path.join(user_dir(sid or 'default'), "leads.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_leads(leads, sid=None):
    path = os.path.join(user_dir(sid or 'default'), "leads.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(leads, f, indent=2)
    except Exception as e:
        print(f"[Error saving leads] {e}")

def load_jobs(sid=None):
    path = os.path.join(user_dir(sid or 'default'), "jobs.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_jobs(jobs, sid=None):
    path = os.path.join(user_dir(sid or 'default'), "jobs.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(jobs, f, indent=2)
    except Exception as e:
        print(f"[Error saving jobs] {e}")

def load_candidate_profile(sid=None):
    path = os.path.join(user_dir(sid or 'default'), "profile.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}   # Empty — user fills their own profile on first use

def save_candidate_profile(profile, sid=None):
    path = os.path.join(user_dir(sid or 'default'), "profile.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2)
    except Exception as e:
        print(f"[Error saving profile] {e}")

def load_smtp_config():
    if os.path.exists(SMTP_FILE):
        try:
            with open(SMTP_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "host": "smtp.gmail.com",
        "port": 587,
        "username": "",
        "password": "",
        "from_name": "",
        "from_email": ""
    }

def save_smtp_config(config, sid=None):
    path = os.path.join(user_dir(sid or 'default'), "smtp_config.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"[Error saving SMTP] {e}")

# --- ROUTES ---
@app.route("/")
def index():
    return render_template("index.html")

# ================= JOB & HR SCRAPER ENDPOINTS =================
@app.route("/api/jobs/scrape/start", methods=["POST"])
def start_job_scrape():
    if state['job_scraper']['running']:
        return jsonify({"success": False, "message": "Job scraper is already running!"}), 400
        
    data = request.json or {}
    role = data.get("role", "").strip()
    location = data.get("location", "").strip()
    country = data.get("country", "").strip()
    target_count = int(data.get("target_count", 15))
    
    if not role:
        return jsonify({"success": False, "message": "Job role/title is required!"}), 400
        
    stop_event = threading.Event()
    state['job_scraper']['running'] = True
    state['job_scraper']['logs'] = []
    state['job_scraper']['current_count'] = 0
    state['job_scraper']['target_count'] = target_count
    state['job_scraper']['stop_event'] = stop_event

    def worker():
        def callback(event):
            if isinstance(event, dict):
                if event.get('type') == 'log':
                    state['job_scraper']['logs'].append(event.get('message', ''))
                    if len(state['job_scraper']['logs']) > LOGS_MAX:
                        state['job_scraper']['logs'].pop(0)
                elif event.get('type') == 'job_found':
                    job_lead = event.get('job')
                    jobs = load_jobs()
                    # Deduplicate by job_url or (company + title)
                    if not any(j.get('job_url') == job_lead.get('job_url') or 
                              (j.get('company_name', '').lower() == job_lead.get('company_name', '').lower() and 
                               j.get('job_title', '').lower() == job_lead.get('job_title', '').lower()) 
                              for j in jobs):
                        jobs.insert(0, job_lead)
                        save_jobs(jobs)
                    state['job_scraper']['current_count'] = event.get('count', len(jobs))
                elif event.get('type') == 'complete':
                    state['job_scraper']['running'] = False
            else:
                state['job_scraper']['logs'].append(str(event))

        try:
            find_jobs_and_hr(role, location=location, country=country, target_count=target_count, status_callback=callback, stop_event=stop_event)
        except Exception as e:
            state['job_scraper']['logs'].append(f"Job Sniper Error: {str(e)}")
        finally:
            state['job_scraper']['running'] = False

    t = threading.Thread(target=worker, daemon=True)
    state['job_scraper']['thread'] = t
    t.start()

    return jsonify({"success": True, "message": "Global Job & HR Sniper started!"})

@app.route("/api/jobs/scrape/stop", methods=["POST"])
def stop_job_scrape():
    if state['job_scraper']['running'] and state['job_scraper']['stop_event']:
        state['job_scraper']['stop_event'].set()
        state['job_scraper']['running'] = False
        state['job_scraper']['logs'].append("Job search stopped by user.")
        return jsonify({"success": True, "message": "Job scraper stopped."})
    return jsonify({"success": False, "message": "Job scraper is not running."})

@app.route("/api/jobs/scrape/status")
def job_scrape_status():
    return jsonify({
        "running": state['job_scraper']['running'],
        "logs": state['job_scraper']['logs'],
        "current_count": state['job_scraper']['current_count'],
        "target_count": state['job_scraper']['target_count']
    })

# --- JOBS DATABASE MANAGEMENT ---
@app.route("/api/jobs")
def get_jobs():
    return jsonify(load_jobs())

@app.route("/api/jobs/clear", methods=["POST"])
def clear_jobs():
    save_jobs([])
    return jsonify({"success": True, "message": "All job leads cleared."})

@app.route("/api/jobs/delete", methods=["POST"])
def delete_job():
    job_id = request.json.get("id", "")
    jobs = load_jobs()
    new_jobs = [j for j in jobs if j.get("id") != job_id]
    save_jobs(new_jobs)
    return jsonify({"success": True, "jobs": new_jobs})

@app.route("/api/jobs/update-status", methods=["POST"])
def update_job_status():
    data = request.json or {}
    job_id = data.get("id")
    new_status = data.get("status")
    notes = data.get("notes")
    
    jobs = load_jobs()
    for j in jobs:
        if j.get("id") == job_id:
            if new_status:
                j["status"] = new_status
            if notes is not None:
                j["notes"] = notes
            break
    save_jobs(jobs)
    return jsonify({"success": True, "jobs": jobs})

@app.route("/api/jobs/export")
def export_jobs_csv():
    jobs = load_jobs()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Job Title", "Company", "Location", "HR Email", "Application URL", "Company Website", "Status", "Date Found", "LinkedIn HR Search", "Notes"])
    for j in jobs:
        writer.writerow([
            j.get("job_title", ""),
            j.get("company_name", ""),
            j.get("location", ""),
            j.get("hr_email", ""),
            j.get("job_url", ""),
            j.get("company_website", ""),
            j.get("status", "Discovered"),
            j.get("date_found", ""),
            j.get("linkedin_hr", ""),
            j.get("notes", "")
        ])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=job_leads_export.csv"}
    )

# ================= AI CAREER STUDIO & GENERATOR =================
@app.route("/api/career/profile", methods=["GET", "POST"])
def candidate_profile_api():
    if request.method == "POST":
        data = request.json or {}
        save_candidate_profile(data)
        return jsonify({"success": True, "profile": data})
    return jsonify(load_candidate_profile())

@app.route("/api/career/generate", methods=["POST"])
def generate_career_assets():
    data = request.json or {}
    job_title = data.get("job_title", "").strip() or "Business Development Associate"
    company_name = data.get("company_name", "").strip() or "Target Employer"
    job_desc = data.get("job_desc", "").strip()
    hr_email = data.get("hr_email", "").strip()
    
    profile = load_candidate_profile()
    
    resume_data = generate_tailored_resume(job_title, company_name, job_desc, candidate=profile)
    cover_letter = generate_tailored_cover_letter(job_title, company_name, job_desc, candidate=profile)
    cold_emails = generate_tailored_cold_emails(job_title, company_name, hr_email=hr_email, job_desc=job_desc, candidate=profile)
    
    return jsonify({
        "success": True,
        "job_title": job_title,
        "company_name": company_name,
        "track": resume_data["track"],
        "resume_headline": resume_data["headline"],
        "resume_markdown": resume_data["markdown"],
        "resume_html": resume_data["html"],
        "cover_letter": cover_letter,
        "cold_emails": cold_emails
    })

@app.route("/api/career/send-application", methods=["POST"])
def send_single_application():
    data = request.json or {}
    to_email = data.get("to_email", "").strip()
    subject = data.get("subject", "").strip()
    body_text = data.get("body", "").strip()
    
    if not to_email or not subject or not body_text:
        return jsonify({"success": False, "message": "Recipient email, subject, and body are required."}), 400
        
    smtp_cfg = load_smtp_config()
    if not smtp_cfg.get("username") or not smtp_cfg.get("password"):
        return jsonify({"success": False, "message": "Please configure your SMTP settings first."}), 400
        
    try:
        send_single_email(smtp_cfg, to_email, subject, body_text)
        return jsonify({"success": True, "message": f"Application email sent successfully to {to_email}!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to send email: {str(e)}"}), 500

# ================= LEGACY B2B SCRAPER ENDPOINTS =================
@app.route("/api/scrape/start", methods=["POST"])
def start_scrape():
    if state['scraper']['running']:
        return jsonify({"success": False, "message": "Scraper is already running!"}), 400
        
    data = request.json or {}
    niche = data.get("niche", "").strip()
    location = data.get("location", "").strip()
    target_count = int(data.get("target_count", 20))
    
    if not niche:
        return jsonify({"success": False, "message": "Niche is required!"}), 400
        
    stop_event = threading.Event()
    state['scraper']['running'] = True
    state['scraper']['logs'] = []
    state['scraper']['current_count'] = 0
    state['scraper']['target_count'] = target_count
    state['scraper']['stop_event'] = stop_event

    def worker():
        def callback(event):
            if isinstance(event, dict):
                if event.get('type') == 'log':
                    state['scraper']['logs'].append(event.get('message', ''))
                    if len(state['scraper']['logs']) > LOGS_MAX:
                        state['scraper']['logs'].pop(0)
                elif event.get('type') == 'lead_found':
                    lead = event.get('lead')
                    leads = load_leads()
                    if not any(l['email'].lower() == lead['email'].lower() for l in leads):
                        leads.append(lead)
                        save_leads(leads)
                    state['scraper']['current_count'] = event.get('count', len(leads))
                elif event.get('type') == 'complete':
                    state['scraper']['running'] = False
            else:
                state['scraper']['logs'].append(str(event))

        try:
            find_leads(niche, location, target_count, status_callback=callback, stop_event=stop_event)
        except Exception as e:
            state['scraper']['logs'].append(f"Error: {str(e)}")
        finally:
            state['scraper']['running'] = False

    t = threading.Thread(target=worker, daemon=True)
    state['scraper']['thread'] = t
    t.start()

    return jsonify({"success": True, "message": "Scraper started!"})

@app.route("/api/scrape/stop", methods=["POST"])
def stop_scrape():
    if state['scraper']['running'] and state['scraper']['stop_event']:
        state['scraper']['stop_event'].set()
        state['scraper']['running'] = False
        state['scraper']['logs'].append("Stop signal sent.")
        return jsonify({"success": True, "message": "Scraper stopped."})
    return jsonify({"success": False, "message": "Scraper is not running."})

@app.route("/api/scrape/status")
def scrape_status():
    return jsonify({
        "running": state['scraper']['running'],
        "logs": state['scraper']['logs'],
        "current_count": state['scraper']['current_count'],
        "target_count": state['scraper']['target_count']
    })

# --- B2B LEADS MANAGEMENT ---
@app.route("/api/leads")
def get_leads():
    return jsonify(load_leads())

@app.route("/api/leads/clear", methods=["POST"])
def clear_leads():
    save_leads([])
    return jsonify({"success": True, "message": "All leads cleared."})

@app.route("/api/leads/delete", methods=["POST"])
def delete_lead():
    email = request.json.get("email", "").lower()
    leads = load_leads()
    new_leads = [l for l in leads if l.get("email", "").lower() != email]
    save_leads(new_leads)
    return jsonify({"success": True, "leads": new_leads})

@app.route("/api/leads/export")
def export_leads_csv():
    leads = load_leads()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Business Name", "Email", "Website", "Niche", "Location", "Date Found"])
    for l in leads:
        writer.writerow([
            l.get("business_name", ""),
            l.get("email", ""),
            l.get("website", ""),
            l.get("niche", ""),
            l.get("location", ""),
            l.get("date_found", "")
        ])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=leads_export.csv"}
    )

# --- SMTP SETTINGS ---
@app.route("/api/smtp/load")
def get_smtp():
    cfg = load_smtp_config()
    masked = dict(cfg)
    if masked.get("password"):
        masked["password"] = "********"
    return jsonify(masked)

@app.route("/api/smtp/save", methods=["POST"])
def save_smtp():
    data = request.json or {}
    cfg = load_smtp_config()
    for k in ["host", "port", "username", "from_name", "from_email"]:
        if k in data:
            cfg[k] = data[k]
    if data.get("password") and data.get("password") != "********":
        cfg["password"] = data["password"]
    save_smtp_config(cfg)
    return jsonify({"success": True, "message": "SMTP configuration saved."})

@app.route("/api/smtp/test", methods=["POST"])
def test_smtp():
    data = request.json or {}
    cfg = load_smtp_config()
    host = data.get("host") or cfg.get("host")
    port = data.get("port") or cfg.get("port")
    user = data.get("username") or cfg.get("username")
    pwd = data.get("password")
    if not pwd or pwd == "********":
        pwd = cfg.get("password")
    success, msg = verify_smtp_connection(host, port, user, pwd)
    return jsonify({"success": success, "message": msg})

# --- OUTREACH CAMPAIGN ---
@app.route("/api/campaign/start", methods=["POST"])
def start_campaign():
    if state['campaign']['running']:
        return jsonify({"success": False, "message": "A campaign is already running!"}), 400

    data = request.json or {}
    subject = data.get("subject", "")
    body = data.get("body", "")
    delay_min = int(data.get("delay_min", 30))
    delay_max = int(data.get("delay_max", 60))
    selected_emails = data.get("selected_emails", [])

    if not subject or not body:
        return jsonify({"success": False, "message": "Subject and Body are required."}), 400

    leads = load_leads()
    if selected_emails:
        leads_to_send = [l for l in leads if l.get("email") in selected_emails]
    else:
        leads_to_send = leads

    if not leads_to_send:
        return jsonify({"success": False, "message": "No leads selected or available to send."}), 400

    smtp_cfg = load_smtp_config()
    if not smtp_cfg.get("username") or not smtp_cfg.get("password"):
        return jsonify({"success": False, "message": "Please configure your SMTP settings first."}), 400

    stop_event = threading.Event()
    state['campaign']['running'] = True
    state['campaign']['logs'] = []
    state['campaign']['sent'] = 0
    state['campaign']['total'] = len(leads_to_send)
    state['campaign']['stop_event'] = stop_event

    def worker():
        def callback(evt):
            msg = evt.get('message', '')
            state['campaign']['logs'].append(msg)
            if len(state['campaign']['logs']) > LOGS_MAX:
                state['campaign']['logs'].pop(0)
            state['campaign']['sent'] = evt.get('sent', 0)

        try:
            run_campaign(
                leads=leads_to_send,
                smtp_config=smtp_cfg,
                subject_template=subject,
                body_template=body,
                delay_range=(delay_min, delay_max),
                status_callback=callback,
                stop_event=stop_event
            )
        except Exception as e:
            state['campaign']['logs'].append(f"Campaign error: {str(e)}")
        finally:
            state['campaign']['running'] = False

    t = threading.Thread(target=worker, daemon=True)
    state['campaign']['thread'] = t
    t.start()

    return jsonify({"success": True, "message": "Campaign launched!"})

@app.route("/api/campaign/stop", methods=["POST"])
def stop_campaign():
    if state['campaign']['running'] and state['campaign']['stop_event']:
        state['campaign']['stop_event'].set()
        state['campaign']['running'] = False
        state['campaign']['logs'].append("Campaign stopped by user.")
        return jsonify({"success": True, "message": "Campaign stopped."})
    return jsonify({"success": False, "message": "Campaign is not running."})

@app.route("/api/campaign/status")
def campaign_status():
    return jsonify({
        "running": state['campaign']['running'],
        "logs": state['campaign']['logs'],
        "sent": state['campaign']['sent'],
        "total": state['campaign']['total']
    })

@app.route("/api/campaign/history")
def campaign_history():
    return jsonify(load_sent_history())

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    host = "0.0.0.0"
    print("=" * 65)
    print(" CareerSniper AI Suite — Global Public Service")
    print(f" Server live on: http://{host}:{port}")
    print("=" * 65)
    app.run(host=host, port=port, debug=False)
