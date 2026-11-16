import re
import time
import random
import urllib.parse
import urllib3
import requests
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Aggregator, social media, and directory domains to ignore (we want direct business sites)
AGGREGATOR_DOMAINS = {
    'yelp.com', 'yellowpages.com', 'tripadvisor.com', 'facebook.com', 
    'instagram.com', 'linkedin.com', 'twitter.com', 'x.com', 'youtube.com', 
    'wikipedia.org', 'tiktok.com', 'pinterest.com', 'reddit.com', 'bbb.org', 
    'mapquest.com', 'zocdoc.com', 'healthgrades.com', 'angi.com', 
    'thumbtack.com', 'houzz.com', 'zoominfo.com', 'dnb.com', 'crunchbase.com',
    'glassdoor.com', 'indeed.com', 'apple.com', 'google.com', 'forbes.com',
    'clutch.co', 'expertise.com', 'upwork.com', 'fiverr.com', 'freelancer.com',
    'trustpilot.com', 'capterra.com', 'g2.com', 'goodfirms.co', 'themanifest.com',
    'designrush.com', 'hubspot.com', 'medium.com', 'quora.com', 'yahoo.com',
    'bing.com', 'microsoft.com', 'msn.com', 'uservoice.com', 'here.com',
    'sortlist.com', 'upcity.com', 'bark.com', 'digitalagencynetwork.com'
}

# Junk / platform keywords in emails
JUNK_EMAIL_KEYWORDS = {
    'sentry.io', 'wixpress.com', 'cloudflare', 'example.com', 'yourdomain.com',
    'domain.com', 'wordpress.org', 'github.com', 'googleapis.com', 'schema.org',
    'bootstrap.com', 'jquery.com', 'fontawesome', 'polyfill', 'wix.com',
    'squarespace.com', 'godaddy.com', 'myshopify.com', 'namecheap.com',
    'gravatar.com', 'doubleclick.net', 'google-analytics.com', 'email.com',
    'test.com', 'sample.com', 'user@domain.com', 'latofonts.com', 'typekit.com'
}

DUMMY_USERNAMES = {'user', 'name', 'yourname', 'test', 'sample', 'admin@example', 'info@example'}

IMAGE_EXTENSIONS = (
    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico', 
    '.css', '.js', '.woff', '.woff2', '.ttf', '.eot', '.pdf', '.mp4'
)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

def clean_email(email_str):
    if not email_str:
        return None
    email_str = email_str.strip().rstrip('.,;:!?)>"\'')
    
    # Must match standard email pattern with strictly alphabetic TLD (2-12 letters)
    match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.([a-zA-Z]{2,12})', email_str)
    if not match:
        return None
    cleaned = match.group(0).lower()
    
    if any(cleaned.endswith(ext) for ext in IMAGE_EXTENSIONS):
        return None
        
    parts = cleaned.split('@')
    user_part = parts[0]
    domain_part = parts[-1]
    
    # Filter dummy emails
    if user_part in DUMMY_USERNAMES or domain_part in {'domain.com', 'example.com', 'email.com', 'test.com'}:
        return None
        
    if 'font' in domain_part or 'theme' in domain_part:
        return None
        
    # Filter NPM packages / version numbers
    tld = domain_part.split('.')[-1]
    if not tld.isalpha() or len(tld) < 2:
        return None
        
    if any(junk in domain_part for junk in JUNK_EMAIL_KEYWORDS):
        return None
        
    if len(user_part) < 2 or len(domain_part) < 4:
        return None
        
    # Filter garbage hashes
    if len(user_part) > 28 or 'u00' in user_part or ('20' in user_part and len(user_part) > 15):
        return None
        
    return cleaned

def clean_business_name(raw_title, domain=""):
    if not raw_title:
        if domain:
            return domain.split('.')[0].replace('-', ' ').title()
        return "Business Owner"
        
    title = re.split(r'[-–—|:]', raw_title)[0].strip()
    # Remove common prefixes like "Website", "Home", etc.
    if title.lower() in {'website', 'home', 'official site', 'contact'}:
        if domain:
            return domain.split('.')[0].replace('-', ' ').title()
    if len(title) < 2 or len(title) > 50:
        if domain:
            return domain.split('.')[0].replace('-', ' ').title()
        return "Business Owner"
    return title

def extract_domain(url):
    try:
        parsed = urllib.parse.urlparse(url)
        netloc = parsed.netloc.lower()
        if netloc.startswith('www.'):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return ""

def is_valid_target_url(url):
    domain = extract_domain(url)
    if not domain or '.' not in domain:
        return False
    for bad in AGGREGATOR_DOMAINS:
        if domain == bad or domain.endswith('.' + bad):
            return False
    return True

def search_yahoo(query, max_results=30):
    """
    Scrapes Yahoo search results with URL decoding and pagination.
    Works consistently across ANY niche (local, online, B2B, e-commerce, services).
    """
    results = []
    seen_domains = set()
    
    # Iterate across pages (page 1, 11, 21)
    for page_offset in [1, 11, 21]:
        if len(results) >= max_results:
            break
        try:
            params = {'p': query, 'b': page_offset}
            resp = requests.get('https://search.yahoo.com/search', params=params, headers=HEADERS, timeout=8)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if '/RU=' in href:
                        try:
                            ru = urllib.parse.unquote(href.split('/RU=')[1].split('/RK=')[0])
                            if not ru.startswith('http') or any(b in ru for b in ['bing.com', 'yahoo.com', 'google.com']):
                                continue
                            domain = extract_domain(ru)
                            if domain and is_valid_target_url(ru) and domain not in seen_domains:
                                seen_domains.add(domain)
                                title = a.get_text(strip=True)
                                results.append({
                                    'title': title,
                                    'url': ru,
                                    'domain': domain
                                })
                                if len(results) >= max_results:
                                    break
                        except Exception:
                            pass
        except Exception as e:
            print(f"[Yahoo Search Error] {e}")
            break
        time.sleep(0.5)
        
    return results

def crawl_site_for_emails(site_url):
    """
    Crawls homepage and contact subpages of a business website to extract verified emails.
    """
    found_emails = set()
    visited_urls = set()
    
    parsed = urllib.parse.urlparse(site_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    
    urls_to_check = [site_url]
    
    # 1. Fetch homepage
    try:
        resp = requests.get(site_url, headers=HEADERS, verify=False, timeout=6)
        visited_urls.add(site_url)
        
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Check mailto links
            for a in soup.find_all('a', href=True):
                href = a['href'].strip()
                if href.lower().startswith('mailto:'):
                    email_raw = href.split('?')[0].replace('mailto:', '').strip()
                    cleaned = clean_email(email_raw)
                    if cleaned:
                        found_emails.add(cleaned)
                        
            # Check regex in body
            for raw_match in re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,12}', resp.text):
                cleaned = clean_email(raw_match)
                if cleaned:
                    found_emails.add(cleaned)
                    
            # Check contact/about links for sub-pages
            for a in soup.find_all('a', href=True):
                href = a['href'].strip()
                href_lower = href.lower()
                if any(k in href_lower for k in ['contact', 'about', 'touch', 'team', 'staff']):
                    full_link = urllib.parse.urljoin(base_url, href)
                    if urllib.parse.urlparse(full_link).netloc == parsed.netloc:
                        if full_link not in visited_urls and len(urls_to_check) < 3:
                            urls_to_check.append(full_link)
                            
    except Exception:
        pass
        
    # 2. Check contact sub-page if no email was found on homepage
    if not found_emails:
        for sub_url in urls_to_check[1:]:
            if sub_url in visited_urls:
                continue
            visited_urls.add(sub_url)
            try:
                sub_resp = requests.get(sub_url, headers=HEADERS, verify=False, timeout=6)
                if sub_resp.status_code == 200:
                    sub_soup = BeautifulSoup(sub_resp.text, 'html.parser')
                    for a in sub_soup.find_all('a', href=True):
                        href = a['href'].strip()
                        if href.lower().startswith('mailto:'):
                            c = clean_email(href.split('?')[0].replace('mailto:', ''))
                            if c:
                                found_emails.add(c)
                    for raw_match in re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,12}', sub_resp.text):
                        c = clean_email(raw_match)
                        if c:
                            found_emails.add(c)
                if found_emails:
                    break
            except Exception:
                continue
                
    return list(found_emails)

def generate_queries(niche, location=""):
    """
    Generates natural, high-converting search queries for any niche.
    """
    niche = niche.strip()
    loc = location.strip()
    
    if loc:
        return [
            f"{niche} in {loc}",
            f"{niche} {loc} contact us",
            f"best {niche} companies in {loc}",
            f"top {niche} services {loc}",
            f"{niche} {loc} email",
        ]
    else:
        return [
            f"{niche} agency",
            f"{niche} companies contact us",
            f"best {niche} services",
            f"{niche} firms contact",
            f"top {niche} specialists email",
        ]

def find_leads(niche, location="", target_count=20, status_callback=None, stop_event=None):
    """
    Universal Lead Finder engine:
    1. Searches the live web using query expansion across any niche.
    2. Identifies target business websites (filtering out directories & aggregators).
    3. Deep-crawls homepages and contact pages for verified business emails.
    4. Validates, deduplicates, and logs leads live.
    """
    def log(msg):
        if status_callback:
            status_callback({'type': 'log', 'message': msg})
        print(f"[LeadSniper] {msg}")

    loc_label = f" in {location}" if location.strip() else " (Global / Online)"
    log(f"Starting discovery for: '{niche}{loc_label}' (Target: {target_count})")
    
    collected_leads = []
    seen_emails = set()
    seen_domains = set()
    
    queries = generate_queries(niche, location)
    
    for q_idx, query in enumerate(queries):
        if stop_event and stop_event.is_set():
            log("Discovery stopped by user.")
            break
            
        if len(collected_leads) >= target_count:
            break
            
        log(f"Searching web (Strategy {q_idx + 1}/{len(queries)}): '{query}'...")
        candidates = search_yahoo(query, max_results=25)
        log(f"Discovered {len(candidates)} candidate business websites.")
        
        for biz in candidates:
            if stop_event and stop_event.is_set():
                break
                
            if len(collected_leads) >= target_count:
                break
                
            url = biz['url']
            domain = biz['domain']
            raw_title = biz['title']
            
            if domain in seen_domains:
                continue
            seen_domains.add(domain)
            
            biz_name = clean_business_name(raw_title, domain)
            log(f"Inspecting website: {domain} ({biz_name})...")
            
            crawled_emails = crawl_site_for_emails(url)
            
            for em in crawled_emails:
                if em not in seen_emails:
                    seen_emails.add(em)
                    lead = {
                        'business_name': biz_name,
                        'email': em,
                        'website': f"https://{domain}",
                        'niche': niche,
                        'location': location if location.strip() else "Global",
                        'date_found': time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    collected_leads.append(lead)
                    log(f"✓ Found Lead: {biz_name} | {em}")
                    if status_callback:
                        status_callback({
                            'type': 'lead_found', 
                            'lead': lead, 
                            'count': len(collected_leads),
                            'target': target_count
                        })
                        
                    if len(collected_leads) >= target_count:
                        break
                        
        time.sleep(1.0)
        
    log(f"Discovery complete! Total verified leads found: {len(collected_leads)}")
    if status_callback:
        status_callback({'type': 'complete', 'total': len(collected_leads)})
    return collected_leads

if __name__ == "__main__":
    leads = find_leads("Marketing Agency", "Austin TX", target_count=3)
    print("\nVerified Leads:")
    for l in leads:
        print(l)
