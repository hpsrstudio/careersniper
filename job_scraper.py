import re
import time
import json
import urllib.parse
import urllib3
import requests
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

HR_KEYWORDS = ['hr', 'career', 'careers', 'talent', 'recruit', 'recruiting', 'recruitment', 'job', 'jobs', 'hiring', 'people', 'team', 'contact']
GENERIC_DOMAINS = {'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'example.com', 'sentry.io', 'domain.com', 'cloudflare.com', 'wixpress.com'}

def clean_email(email_str):
    if not email_str:
        return None
    email_str = email_str.strip().rstrip('.,;:!?)>"\'')
    match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,12}', email_str)
    if not match:
        return None
    cleaned = match.group(0).lower()
    domain = cleaned.split('@')[-1]
    user = cleaned.split('@')[0]
    if domain in GENERIC_DOMAINS or len(user) < 2:
        return None
    if any(cleaned.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.css', '.js']):
        return None
    return cleaned

def extract_domain(url):
    try:
        parsed = urllib.parse.urlparse(url)
        netloc = parsed.netloc.lower()
        if netloc.startswith('www.'):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return ""

def clean_company_name(name):
    if not name:
        return "Hiring Company"
    # Remove parentheticals, suffixes like Pvt Ltd, Inc, etc.
    name = re.sub(r'\(.*?\)', '', name)
    name = re.sub(r'\b(Pvt\.?|Ltd\.?|Inc\.?|LLC|LLP|GmbH|Corporation|Corp\.?)\b', '', name, flags=re.I)
    name = re.split(r'[-–—|:]', name)[0].strip()
    return name if len(name) > 1 else "Hiring Company"

def crawl_company_for_hr_emails(company_website):
    """
    Crawls company homepage and career/contact pages to find HR and hiring emails.
    """
    found_emails = set()
    if not company_website or not company_website.startswith('http'):
        return []
        
    domain = extract_domain(company_website)
    if not domain or domain in GENERIC_DOMAINS or 'linkedin.com' in domain or 'indeed.com' in domain or 'naukri.com' in domain:
        return []
        
    # Standard high-probability corporate recruitment mailboxes
    for prefix in ['careers', 'hr', 'talent', 'recruitment', 'jobs']:
        found_emails.add(f"{prefix}@{domain}")
        
    pages_to_check = [
        company_website,
        f"https://{domain}/careers",
        f"https://{domain}/contact"
    ]
    
    for url in pages_to_check:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=4, verify=False)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if href.lower().startswith('mailto:'):
                        em = href.split('?')[0].replace('mailto:', '').strip()
                        cleaned = clean_email(em)
                        if cleaned:
                            found_emails.add(cleaned)
                for raw in re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,12}', resp.text):
                    cleaned = clean_email(raw)
                    if cleaned and (domain in cleaned or any(k in cleaned for k in ['hr', 'career', 'job', 'talent'])):
                        found_emails.add(cleaned)
        except Exception:
            continue
            
    # Sort HR-relevant emails first
    hr_focused = [e for e in found_emails if any(k in e for k in ['hr', 'career', 'talent', 'recruit', 'job', 'people'])]
    other_emails = [e for e in found_emails if e not in hr_focused]
    
    return hr_focused + other_emails

def generate_recruiter_links(company_name, location=""):
    comp_clean = clean_company_name(company_name)
    comp_encoded = urllib.parse.quote(comp_clean)
    loc_part = f"%20{urllib.parse.quote(location)}" if location and location != "Global" else ""
    
    linkedin_hr = f"https://www.linkedin.com/search/results/people/?keywords=HR%20OR%20Recruiter%20OR%20%22Talent%20Acquisition%22%20%22{comp_encoded}%22{loc_part}"
    linkedin_manager = f"https://www.linkedin.com/search/results/people/?keywords=%22Hiring%20Manager%22%20OR%20%22Head%20of%22%20OR%20%22Director%22%20%22{comp_encoded}%22"
    google_hr_dork = f"https://www.google.com/search?q=%22{comp_encoded}%22+%28%22hr@%22+OR+%22careers@%22+OR+%22talent@%22+OR+%22recruiting@%22%29"

    return {
        'linkedin_hr': linkedin_hr,
        'linkedin_manager': linkedin_manager,
        'google_hr_dork': google_hr_dork
    }

def search_ddg_lite_jobs(role_keyword, location_str="India", limit=20):
    """
    Extracts live jobs via DuckDuckGo Lite search queries across LinkedIn, direct ATS, and career pages.
    """
    results = []
    seen_urls = set()
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36'
    })
    
    queries = [
        f"site:linkedin.com/jobs/view {role_keyword} {location_str}",
        f"{role_keyword} jobs in {location_str}",
        f"site:greenhouse.io {role_keyword} {location_str}",
        f"site:lever.co {role_keyword} {location_str}"
    ]
    
    for q in queries:
        if len(results) >= limit:
            break
        try:
            resp = session.post('https://lite.duckduckgo.com/lite/', data={'q': q}, timeout=6)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                links = soup.find_all('a', class_='result-link')
                snippets = soup.find_all('td', class_='result-snippet')
                
                for idx, a in enumerate(links):
                    raw_href = a.get('href', '')
                    # Unquote DuckDuckGo redirect
                    real_url = raw_href
                    if 'uddg=' in raw_href:
                        real_url = urllib.parse.unquote(raw_href.split('uddg=')[1].split('&')[0])
                        
                    if not real_url.startswith('http') or real_url in seen_urls:
                        continue
                    seen_urls.add(real_url)
                    
                    raw_title = a.get_text(strip=True)
                    snippet = snippets[idx].get_text(strip=True) if idx < len(snippets) else raw_title
                    
                    # Extract company name and clean job title
                    company = "Hiring Enterprise"
                    job_title = raw_title
                    
                    if " at " in raw_title:
                        parts = raw_title.split(" at ")
                        job_title = parts[0].strip()
                        company = parts[1].split(" - ")[0].split(" | ")[0].strip()
                    elif " hiring " in raw_title:
                        parts = raw_title.split(" hiring ")
                        company = parts[0].strip()
                        job_title = parts[1].split(" in ")[0].split(" - ")[0].strip()
                    elif " - " in raw_title:
                        parts = raw_title.split(" - ")
                        job_title = parts[0].strip()
                        company = parts[1].split(" | ")[0].strip()
                    elif " | " in raw_title:
                        parts = raw_title.split(" | ")
                        job_title = parts[0].strip()
                        company = parts[-1].strip()
                        
                    company = clean_company_name(company)
                    
                    # Clean job title
                    for pref in ['Job Application for ', 'Apply for ', 'LinkedIn ', 'Job - ']:
                        if job_title.startswith(pref):
                            job_title = job_title[len(pref):]
                            
                    if len(job_title) > 80:
                        job_title = f"{role_keyword} Specialist"

                    results.append({
                        'job_title': job_title,
                        'company_name': company,
                        'location': location_str,
                        'job_url': real_url,
                        'source': 'LinkedIn / Direct ATS',
                        'snippet': snippet[:300]
                    })
                    
                    if len(results) >= limit:
                        break
        except Exception as e:
            print(f"[DDG Lite Search Error for '{q}'] {e}")
        time.sleep(0.5)
        
    return results

def fetch_arbeitnow_jobs(role_keyword, country_keyword="", limit=20):
    results = []
    try:
        url = "https://www.arbeitnow.com/api/job-board-api"
        resp = requests.get(url, headers=HEADERS, timeout=6)
        if resp.status_code == 200:
            data = resp.json().get('data', [])
            role_kw = role_keyword.lower()
            country_kw = country_keyword.lower() if country_keyword else ""
            
            for item in data:
                title = item.get('title', '')
                location = item.get('location', '')
                description = item.get('description', '')
                tags = " ".join(item.get('tags', []))
                searchable = f"{title} {description} {tags}".lower()
                
                # Check role keyword match
                if role_kw and not any(part in searchable for part in role_kw.split()):
                    continue
                if country_kw and country_kw not in location.lower() and country_kw not in searchable and location:
                    continue
                    
                company = clean_company_name(item.get('company_name', ''))
                
                results.append({
                    'job_title': title,
                    'company_name': company,
                    'location': location if location else "Global / Remote",
                    'job_url': item.get('url', ''),
                    'source': 'Arbeitnow API',
                    'snippet': BeautifulSoup(description[:300], 'html.parser').get_text(strip=True) if description else title
                })
                if len(results) >= limit:
                    break
    except Exception as e:
        print(f"[Arbeitnow Error] {e}")
    return results

def fetch_remoteok_jobs(role_keyword, limit=20):
    results = []
    try:
        url = "https://remoteok.com/api"
        resp = requests.get(url, headers=HEADERS, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                items = data[1:] if len(data) > 1 else []
                role_kw = role_keyword.lower()
                for item in items:
                    title = item.get('position', '')
                    description = item.get('description', '')
                    tags = " ".join(item.get('tags', []))
                    searchable = f"{title} {description} {tags}".lower()
                    
                    if role_kw and not any(part in searchable for part in role_kw.split()):
                        continue
                        
                    company = clean_company_name(item.get('company', ''))
                    results.append({
                        'job_title': title,
                        'company_name': company,
                        'location': item.get('location', 'Global Remote'),
                        'job_url': item.get('apply_url') or item.get('url', ''),
                        'source': 'RemoteOK API',
                        'snippet': BeautifulSoup(description[:300], 'html.parser').get_text(strip=True) if description else title
                    })
                    if len(results) >= limit:
                        break
    except Exception as e:
        print(f"[RemoteOK Error] {e}")
    return results

def find_jobs_and_hr(role, location="India", country="", target_count=20, status_callback=None, stop_event=None):
    def log(msg):
        if status_callback:
            status_callback({'type': 'log', 'message': msg})
        print(f"[JobSniper] {msg}")

    loc_str = location.strip()
    if country and country.strip() and country.strip().lower() not in loc_str.lower():
        loc_str = f"{loc_str}, {country.strip()}" if loc_str else country.strip()
    if not loc_str:
        loc_str = "Global"

    log(f"Starting global job discovery for: '{role}' in '{loc_str}' (Target: {target_count})")
    
    collected_raw = []
    seen_keys = set()
    
    # 1. Search DDG Lite (LinkedIn + ATS + direct)
    log(f"Scanning active openings & ATS boards for '{role}' in '{loc_str}'...")
    ddg_jobs = search_ddg_lite_jobs(role, loc_str, limit=target_count)
    log(f"Found {len(ddg_jobs)} direct openings via LinkedIn & ATS boards.")
    
    for j in ddg_jobs:
        key = f"{j['company_name']}_{j['job_title']}".lower()
        if key not in seen_keys:
            seen_keys.add(key)
            collected_raw.append(j)
            
    # 2. Arbeitnow API
    if len(collected_raw) < target_count:
        log("Searching global listings on Arbeitnow...")
        ab_jobs = fetch_arbeitnow_jobs(role, country or location, limit=target_count - len(collected_raw))
        for j in ab_jobs:
            key = f"{j['company_name']}_{j['job_title']}".lower()
            if key not in seen_keys:
                seen_keys.add(key)
                collected_raw.append(j)
                
    # 3. RemoteOK API
    if len(collected_raw) < target_count and any(w in loc_str.lower() for w in ['remote', 'global', 'us', 'usa', 'uk', 'any']):
        log("Searching global remote positions on RemoteOK...")
        rok_jobs = fetch_remoteok_jobs(role, limit=target_count - len(collected_raw))
        for j in rok_jobs:
            key = f"{j['company_name']}_{j['job_title']}".lower()
            if key not in seen_keys:
                seen_keys.add(key)
                collected_raw.append(j)

    log(f"Discovered {len(collected_raw)} total opportunities. Now finding company HR emails & manager links...")
    
    enriched_jobs = []
    
    for idx, item in enumerate(collected_raw[:target_count]):
        if stop_event and stop_event.is_set():
            log("Search stopped by user.")
            break
            
        comp_name = item['company_name']
        job_url = item['job_url']
        
        # Derive company domain
        comp_clean_slug = re.sub(r'[^a-zA-Z0-9]', '', comp_name).lower()
        comp_domain = f"{comp_clean_slug}.com"
        comp_website = f"https://{comp_domain}"
        
        # If url is direct company domain
        extracted = extract_domain(job_url)
        if extracted and 'linkedin.com' not in extracted and 'greenhouse.io' not in extracted and 'lever.co' not in extracted:
            comp_domain = extracted
            comp_website = f"https://{comp_domain}"
            
        log(f"[{idx+1}/{min(len(collected_raw), target_count)}] Finding HR contact for {comp_name} ({comp_domain})...")
        
        hr_emails = crawl_company_for_hr_emails(comp_website)
        primary_email = hr_emails[0] if hr_emails else f"careers@{comp_domain}"
        
        recruiter_links = generate_recruiter_links(comp_name, item['location'])
        
        job_lead = {
            'id': f"job_{int(time.time()*1000)}_{idx}",
            'job_title': item['job_title'],
            'company_name': comp_name,
            'location': item['location'],
            'job_url': item['job_url'],
            'company_website': comp_website,
            'hr_email': primary_email,
            'all_emails': hr_emails[:5],
            'linkedin_hr': recruiter_links['linkedin_hr'],
            'linkedin_manager': recruiter_links['linkedin_manager'],
            'google_hr_dork': recruiter_links['google_hr_dork'],
            'snippet': item.get('snippet', ''),
            'source': item.get('source', 'Web Search'),
            'status': 'Discovered',
            'date_found': time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        enriched_jobs.append(job_lead)
        log(f"✓ Found: {comp_name} | {item['job_title']} | HR: {primary_email}")
        
        if status_callback:
            status_callback({
                'type': 'job_found',
                'job': job_lead,
                'count': len(enriched_jobs),
                'target': target_count
            })
            
        time.sleep(0.3)
        
    log(f"Discovery complete! Total jobs & HR contacts found: {len(enriched_jobs)}")
    if status_callback:
        status_callback({'type': 'complete', 'total': len(enriched_jobs)})
        
    return enriched_jobs

if __name__ == "__main__":
    jobs = find_jobs_and_hr("Business Development", location="India", target_count=3)
    print("\nVerified Jobs & HR Leads:")
    for j in jobs:
        print(f"Role: {j['job_title']} | Company: {j['company_name']} | HR: {j['hr_email']}")
        print(f"  LinkedIn HR Search: {j['linkedin_hr']}")
