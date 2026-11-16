# 🎯 LeadSniper: Universal Lead Finder & Cold Email Outreach

A complete local application designed to find verified business leads in **any niche** and launch automated, personalized cold outreach campaigns without triggering spam filters.

---

## ⚡ Quick Start (1-Click Run)

1. Double-click **`run.bat`** (or open PowerShell in this folder and run `python app.py`).
2. Open your browser to: **[http://localhost:5000](http://localhost:5000)**.

---

## 🛠 Features

### 1. 🔍 Universal Lead Finder
* **Any Niche:** Enter any industry (e.g. *Roofing Contractors, SaaS Marketing, Dentists, Real Estate, Gyms, Plumbers*).
* **Targeted Location:** Specify any city/country (e.g. *Austin TX, London, Miami*) or leave it blank to automatically search across top commercial hubs worldwide.
* **Smart Website & Email Extractor:** Discovers business entities, extracts contact info from public directory records, and deep-crawls company websites (homepage, `/contact`, `/about`) for verified decision-maker emails.
* **Live Discovery Console:** Watch real-time discovery logs, progress bars, and extracted leads.

### 2. 📋 Leads Database & CSV Export
* Review all discovered business leads in a clean dashboard.
* Select, filter, or delete individual leads.
* **1-Click CSV Export:** Export leads to CSV for Excel, Google Sheets, or CRM import.

### 3. ✉️ Cold Email Outreach Engine
* **Pre-made High-Converting Templates:**
  * *Template 1: Quick Question / Inbound Lead Offer*
  * *Template 2: Free Growth Audit / Bottleneck Fix*
  * *Template 3: Capacity Overflow / White-label Partnership*
* **Dynamic Tag Personalization:** Automatically inserts `{business_name}`, `{website}`, `{niche}`, and `{location}`.
* **Live Personalization Preview:** See how your email will look for each recipient before sending.
* **Anti-Spam Humanized Throttling:** Configurable randomized delay (e.g., 30–60 seconds between sends) so mail servers treat it as human activity.
* **Duplicate Protection:** Automatically logs sent emails to prevent messaging the same address twice.

### 4. ⚙️ SMTP Setup (Gmail, Google Workspace, Outlook, Custom)
* Send directly through Gmail using a free **Google App Password**.
* Or connect any custom domain SMTP (SendGrid, Mailgun, Amazon SES, Namecheap, Outlook).
* Built-in **"Test Connection"** button to verify credentials before launching a campaign.

---

## 💡 How to Get a Free Gmail App Password (1 Minute)
1. Go to your **[Google Account Security](https://myaccount.google.com/security)**.
2. Turn on **2-Step Verification** (if not already enabled).
3. Search for **"App Passwords"** in the top search bar.
4. Name it `LeadSniper` and click **Create**.
5. Copy the 16-character code and paste it into the LeadSniper SMTP settings tab.
