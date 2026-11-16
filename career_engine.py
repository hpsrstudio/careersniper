import re
import json
import os

DEFAULT_CANDIDATE = {
    "full_name": "Harpartap Singh Randhawa",
    "email": "ihpsrofficial@gmail.com",
    "phone": "+91 95014 29560",
    "location": "Punjab, India (Open to Relocation: Gurgaon, Bangalore, Mumbai, Remote & International)",
    "linkedin": "linkedin.com/in/ihpsrofficial",
    "education": [
        {
            "degree": "Master of Business Administration (MBA) – Capital Markets (Marketing & Finance)",
            "institution": "University Institute of Applied Management Sciences (UIAMS), Panjab University, Chandigarh",
            "period": "2022 – 2024",
            "highlights": "Specialized coursework: Financial Modeling, Portfolio Management, Equity Research, B2B Marketing, Consumer Behaviour, Market Analysis."
        },
        {
            "degree": "Bachelor of Business Administration (BBA)",
            "institution": "Global Group of Institutes, Amritsar",
            "period": "2017 – 2020",
            "highlights": "Foundations in Business Management, Corporate Accounting, Organizational Behaviour, Marketing Strategy."
        }
    ],
    "experience": [
        {
            "role": "Operations & Recruitment Intern",
            "company": "Infotechnogen Pvt. Ltd.",
            "period": "June 2023 – August 2023",
            "points": [
                "Screened and evaluated 300+ candidate profiles across technical, sales, and corporate operational roles against specific job descriptions.",
                "Coordinated end-to-end interview schedules for 80+ candidates, reducing average scheduling turnaround time by 25%.",
                "Managed candidate tracking databases and assisted with onboarding documentation and orientation for 15+ new corporate hires.",
                "Collaborated directly with department heads to understand headcount requirements and refine recruitment sourcing criteria."
            ]
        }
    ],
    "leadership": [
        {
            "role": "Head of Media & Visual Communication",
            "organization": "Magestemo Student Club, UIAMS, Panjab University",
            "period": "2022 – 2024",
            "points": [
                "Led a 6-member media team responsible for visual identity, branding, and event photography across 10+ inter-university conferences and business fests.",
                "Designed 40+ high-engagement digital creatives using Canva and Adobe Photoshop, driving a 45% increase in student club participation."
            ]
        },
        {
            "role": "General Body Member",
            "organization": "Rotaract Club of Chandigarh",
            "period": "2023 – 2024",
            "points": [
                "Participated in community outreach programs and youth leadership seminars focusing on organizational leadership and social impact."
            ]
        }
    ],
    "certifications": [
        "Data Science & Artificial Intelligence Bootcamp | UIAMS, Panjab University (2023)",
        "Financial Statement Analysis & Capital Markets Foundations | UIAMS Coursework",
        "CRM & Inbound Lead Generation Principles"
    ]
}

def detect_role_track(job_title, job_desc=""):
    combined = f"{job_title} {job_desc}".lower()
    
    if any(k in combined for k in ['finance', 'financial', 'equity', 'capital market', 'investment', 'analyst', 'valuation', 'accounting', 'portfolio']):
        return "FINANCE"
    elif any(k in combined for k in ['marketing', 'growth', 'brand', 'social media', 'content', 'seo', 'campaign', 'creative']):
        return "MARKETING"
    elif any(k in combined for k in ['operation', 'operations', 'project', 'process', 'supply', 'logistics', 'analyst']):
        return "OPERATIONS"
    elif any(k in combined for k in ['hr', 'recruiter', 'talent', 'people', 'staffing']):
        return "HR"
    else:
        # Default high-yield MBA track
        return "BUSINESS_DEVELOPMENT"

def generate_tailored_resume(job_title, company_name, job_desc="", candidate=None):
    if not candidate:
        candidate = DEFAULT_CANDIDATE
        
    track = detect_role_track(job_title, job_desc)
    
    # Track-specific customizations
    if track == "BUSINESS_DEVELOPMENT":
        headline = f"BUSINESS DEVELOPMENT & CLIENT ACQUISITION SPECIALIST | MBA"
        summary = (
            f"Results-driven MBA graduate specializing in Marketing & Capital Markets, equipped with hands-on "
            f"experience in client prospecting, pipeline development, and B2B communication. Proven ability to research target accounts, "
            f"qualify decision-makers, and execute multi-channel outreach. Eager to leverage strong relationship-building and analytical "
            f"skills to accelerate revenue pipeline and client acquisition as a {job_title} at {company_name}."
        )
        skills = {
            "Core Competencies": "Business Development, Lead Generation, B2B Prospecting, Account Research, Pipeline Management, Client Relationship Management (CRM), Cold Outreach Strategy, Market Analysis",
            "Analytical & Technical": "MS Excel (VLOOKUP, Pivot Tables, Data Cleansing), Power BI (Data Visualization & Dashboards), CRM Workflow Automation, MS PowerPoint, Canva, Adobe Photoshop",
            "Professional Strengths": "Strategic Negotiation, Cross-Functional Communication, Consultative Selling, Problem-Solving, Team Leadership"
        }
        projects = [
            {
                "title": f"B2B Lead Generation & Account Qualification Framework",
                "org": "UIAMS Practical Business Strategy",
                "points": [
                    "Designed an automated multi-step outreach workflow targeting 500+ corporate decision-makers across mid-market enterprises.",
                    "Implemented rigorous ICP (Ideal Customer Profile) qualification filters, achieving a simulated 18% discovery-call conversion rate.",
                    "Built dynamic CRM tracking templates to monitor open rates, reply rates, and lead pipeline velocity."
                ]
            },
            {
                "title": "Market Penetration & Competitive Intelligence Study",
                "org": "Panjab University MBA Research Project",
                "points": [
                    "Analyzed customer acquisition strategies across 6 key competitors in the commercial services and fintech sectors.",
                    "Identified 3 underserved market segments and formulated targeted go-to-market propositions for new product launches."
                ]
            }
        ]
    elif track == "FINANCE":
        headline = f"FINANCIAL ANALYST | CAPITAL MARKETS & VALUATION | MBA"
        summary = (
            f"Analytically rigorous MBA graduate in Capital Markets (Finance & Marketing) from UIAMS, Panjab University. "
            f"Solid grounding in financial modeling, equity analysis, financial statement interpretation, and quantitative risk evaluation. "
            f"Skilled in building analytical models in Excel and synthesizing complex data into actionable executive insights. "
            f"Seeking to contribute high-precision analysis and analytical rigour as a {job_title} at {company_name}."
        )
        skills = {
            "Financial & Analytical": "Financial Modeling, Equity Research, Capital Markets, Valuation (DCF, Relative Valuation), Financial Statement Analysis, Ratio Analysis, Risk Assessment, Portfolio Management",
            "Technical & Data": "Advanced MS Excel (Pivot Tables, VLOOKUP, INDEX/MATCH, Financial Functions, Scenario Manager), Power BI (Financial Dashboards), MS PowerPoint, Statistical Data Analysis",
            "Professional Strengths": "Quantitative Rigor, Commercial Acumen, Financial Reporting, Attention to Detail, Stakeholder Presentation"
        }
        projects = [
            {
                "title": "Comprehensive Equity Valuation & Financial Analysis",
                "org": "UIAMS Capital Markets Specialization Capstone",
                "points": [
                    "Conducted fundamental financial statement analysis and 3-statement financial modeling for leading public firms.",
                    "Built Discounted Cash Flow (DCF) and comparable company valuation models to determine intrinsic share value.",
                    "Prepared a 20-page executive investment thesis covering macroeconomic trends, margin sustainability, and sensitivity analysis."
                ]
            },
            {
                "title": "Portfolio Optimization & Risk-Return Simulator",
                "org": "Panjab University Academic Lab",
                "points": [
                    "Simulated a multi-asset investment portfolio optimizing Sharpe ratio and beta exposure using historical price series in Excel.",
                    "Evaluated portfolio performance across bull, bear, and inflationary market regimes."
                ]
            }
        ]
    elif track == "MARKETING":
        headline = f"MARKETING & GROWTH ASSOCIATE | DIGITAL CAMPAIGNS & BRAND STRATEGY | MBA"
        summary = (
            f"Creative and data-oriented MBA graduate with specialization in Marketing and Capital Markets. "
            f"Hands-on expertise in digital content creation, brand positioning, audience segmentation, and campaign analytics. "
            f"Demonstrated track record of growing audience engagement by 45% through high-impact visual design and storytelling. "
            f"Excited to drive customer acquisition and brand visibility as a {job_title} at {company_name}."
        )
        skills = {
            "Marketing & Growth": "Digital Marketing, Brand Strategy, Inbound Lead Generation, Market Research, Consumer Behavior, Social Media Marketing, Campaign Performance Tracking",
            "Creative & Technical": "Canva (Advanced Visual Assets), Adobe Photoshop, MS Excel (Campaign Analytics & Segmentation), Power BI, MS PowerPoint, Copywriting",
            "Professional Strengths": "Creative Storytelling, Data-Driven Execution, Cross-functional Collaboration, Adaptability"
        }
        projects = [
            {
                "title": "Brand Positioning & Multi-Channel Digital Campaign",
                "org": "UIAMS Marketing Strategy Project",
                "points": [
                    "Conducted primary survey research across 200+ consumer respondents to determine brand recall and purchase triggers.",
                    "Formulated an omni-channel content calendar and designed 25+ visual creatives resulting in a 40% projected lift in brand awareness."
                ]
            }
        ]
    else:
        # Operations / General
        headline = f"OPERATIONS & PROCESS MANAGEMENT ASSOCIATE | MBA"
        summary = (
            f"Detail-oriented MBA graduate specializing in Marketing & Finance with proven operational discipline and organizational agility. "
            f"Hands-on experience optimizing recruitment workflows, screening 300+ candidate profiles, and streamlining team scheduling. "
            f"Skilled in process mapping, KPI tracking, and cross-functional coordination. Seeking to drive operational excellence as a {job_title} at {company_name}."
        )
        skills = {
            "Operations & Management": "Business Operations, Process Optimization, Workflow Mapping, Project Coordination, Cross-Functional Alignment, KPI Monitoring, Resource Planning",
            "Technical Tools": "MS Excel (Data Consolidation, Pivot Tables), Power BI (Operational Dashboards), Process Documentation, MS PowerPoint",
            "Professional Strengths": "Execution Rigor, Problem Solving, Analytical Thinking, Team Collaboration"
        }
        projects = [
            {
                "title": "Recruitment & Onboarding Process Streamlining Framework",
                "org": "Infotechnogen Operational Case Study",
                "points": [
                    "Mapped the candidate intake-to-offer lifecycle, identifying 2 bottlenecks in screening verification.",
                    "Introduced a standardized evaluation rubric and calendar integration that cut coordination lag by 25%."
                ]
            }
        ]

    # Assemble Markdown Resume
    md_lines = [
        f"# {candidate['full_name'].upper()}",
        f"{candidate['location']}",
        f"**Phone:** {candidate['phone']} | **Email:** [{candidate['email']}](mailto:{candidate['email']}) | **LinkedIn:** [{candidate['linkedin']}](https://{candidate['linkedin']})",
        f"\n---\n",
        f"### **{headline}**",
        f"\n{summary}\n",
        f"### **CORE SKILLS & TECHNICAL COMPETENCIES**",
    ]
    
    for cat, sk in skills.items():
        md_lines.append(f"- **{cat}:** {sk}")
        
    md_lines.append(f"\n### **PROFESSIONAL EXPERIENCE**")
    for exp in candidate['experience']:
        md_lines.append(f"**{exp['role']}** | {exp['company']} *({exp['period']})*")
        for pt in exp['points']:
            md_lines.append(f"- {pt}")
            
    md_lines.append(f"\n### **KEY PROJECTS & CASE ANALYSES**")
    for prj in projects:
        md_lines.append(f"**{prj['title']}** | *{prj['org']}*")
        for pt in prj['points']:
            md_lines.append(f"- {pt}")
            
    md_lines.append(f"\n### **EDUCATION**")
    for edu in candidate['education']:
        md_lines.append(f"**{edu['degree']}**  \n{edu['institution']} *({edu['period']})*")
        if edu.get('highlights'):
            md_lines.append(f"- *Key Areas:* {edu['highlights']}")
            
    md_lines.append(f"\n### **LEADERSHIP & EXTRACURRICULAR**")
    for act in candidate['leadership']:
        md_lines.append(f"**{act['role']}** | {act['organization']} *({act['period']})*")
        for pt in act['points']:
            md_lines.append(f"- {pt}")
            
    md_lines.append(f"\n### **CERTIFICATIONS**")
    for cert in candidate['certifications']:
        md_lines.append(f"- {cert}")
        
    resume_markdown = "\n".join(md_lines)
    
    # HTML version for preview and PDF printing
    resume_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{candidate['full_name']} - Resume for {job_title}</title>
        <style>
            body {{ font-family: 'Segoe UI', Helvetica, Arial, sans-serif; line-height: 1.45; color: #1e293b; max-width: 800px; margin: 0 auto; padding: 24px; font-size: 13px; }}
            h1 {{ margin: 0 0 4px 0; font-size: 24px; letter-spacing: 0.5px; color: #0f172a; text-transform: uppercase; text-align: center; }}
            .contact {{ text-align: center; color: #475569; font-size: 12px; margin-bottom: 14px; border-bottom: 1.5px solid #cbd5e1; padding-bottom: 10px; }}
            .headline {{ font-size: 14px; font-weight: 700; color: #2563eb; text-align: center; text-transform: uppercase; margin-bottom: 10px; }}
            h2 {{ font-size: 13px; text-transform: uppercase; color: #0f172a; border-bottom: 1px solid #cbd5e1; padding-bottom: 2px; margin: 14px 0 6px 0; letter-spacing: 0.5px; }}
            p {{ margin: 4px 0; }}
            ul {{ margin: 3px 0 8px 18px; padding: 0; }}
            li {{ margin-bottom: 3px; }}
            .item-header {{ display: flex; justify-content: space-between; font-weight: 600; color: #0f172a; }}
            .sub-header {{ display: flex; justify-content: space-between; font-style: italic; color: #475569; margin-bottom: 3px; font-size: 12px; }}
            @media print {{ body {{ padding: 0; font-size: 11.5px; }} }}
        </style>
    </head>
    <body>
        <h1>{candidate['full_name']}</h1>
        <div class="contact">
            {candidate['location']} | {candidate['phone']} | {candidate['email']} | {candidate['linkedin']}
        </div>
        <div class="headline">{headline}</div>
        
        <h2>Professional Profile</h2>
        <p>{summary}</p>
        
        <h2>Core Skills & Technical Competencies</h2>
        <ul>
            {"".join(f"<li><strong>{cat}:</strong> {val}</li>" for cat, val in skills.items())}
        </ul>
        
        <h2>Professional Experience</h2>
        {"".join(f'''
            <div class="item-header"><span>{exp['role']}</span><span>{exp['period']}</span></div>
            <div class="sub-header"><span>{exp['company']}</span></div>
            <ul>{"".join(f"<li>{pt}</li>" for pt in exp['points'])}</ul>
        ''' for exp in candidate['experience'])}
        
        <h2>Key Projects & Case Analyses</h2>
        {"".join(f'''
            <div class="item-header"><span>{prj['title']}</span><span>{prj['org']}</span></div>
            <ul>{"".join(f"<li>{pt}</li>" for pt in prj['points'])}</ul>
        ''' for prj in projects)}
        
        <h2>Education</h2>
        {"".join(f'''
            <div class="item-header"><span>{edu['degree']}</span><span>{edu['period']}</span></div>
            <div class="sub-header"><span>{edu['institution']}</span></div>
            <ul><li>{edu['highlights']}</li></ul>
        ''' for edu in candidate['education'])}
        
        <h2>Leadership & Extracurricular</h2>
        {"".join(f'''
            <div class="item-header"><span>{act['role']}</span><span>{act['period']}</span></div>
            <div class="sub-header"><span>{act['organization']}</span></div>
            <ul>{"".join(f"<li>{pt}</li>" for pt in act['points'])}</ul>
        ''' for act in candidate['leadership'])}
        
        <h2>Certifications</h2>
        <ul>
            {"".join(f"<li>{cert}</li>" for cert in candidate['certifications'])}
        </ul>
    </body>
    </html>
    """

    return {
        "track": track,
        "headline": headline,
        "markdown": resume_markdown,
        "html": resume_html
    }

def generate_tailored_cover_letter(job_title, company_name, job_desc="", candidate=None):
    if not candidate:
        candidate = DEFAULT_CANDIDATE
        
    track = detect_role_track(job_title, job_desc)
    
    if track == "BUSINESS_DEVELOPMENT":
        skills_pitch = "my specialized MBA coursework in B2B Market Research and Client Acquisition, coupled with hands-on experience in pipeline management and candidate sourcing at Infotechnogen"
        value_pitch = "I have developed strong competencies in identifying decision-makers, navigating CRM systems, and designing tailored outreach campaigns that drive genuine engagement."
    elif track == "FINANCE":
        skills_pitch = "my MBA specialization in Capital Markets (Marketing & Finance) from Panjab University, where I built rigorous foundations in financial valuation, financial statement analysis, and data modeling"
        value_pitch = "Through hands-on projects analyzing equity portfolios and valuation models in Excel and Power BI, I have cultivated the analytical discipline required to evaluate financial data and generate actionable business insights."
    elif track == "MARKETING":
        skills_pitch = "my MBA background combining Capital Markets and Marketing Strategy, combined with practical leadership as Media Head where I scaled club engagement by 45% through high-converting digital assets"
        value_pitch = "I bring a balance of analytical rigor (Excel-driven market segmentation) and creative execution (Canva, Adobe Photoshop) to execute campaigns that elevate brand positioning and drive pipeline growth."
    else:
        skills_pitch = "my MBA education in Business Management and Capital Markets from UIAMS, Panjab University, along with practical experience streamlining workflows and coordinating multi-stakeholder schedules at Infotechnogen"
        value_pitch = "I excel at diagnosing operational friction, structuring data in Excel and Power BI, and executing projects with speed and attention to detail."

    letter = (
        f"Dear Hiring Team at {company_name},\n\n"
        f"I am writing to express my enthusiastic interest in the {job_title} opening at {company_name}. "
        f"Having followed {company_name}'s trajectory and focus on excellence, I am eager to bring my proactive work ethic, "
        f"commercial acumen, and fresh perspective to your team.\n\n"
        f"Recently completing my Master of Business Administration (MBA) in Capital Markets (Marketing & Finance) at UIAMS, Panjab University, "
        f"I have intentionally developed skills that bridge strategic thinking with tangible execution. Specifically, {skills_pitch}. {value_pitch}\n\n"
        f"During my corporate internship at Infotechnogen Pvt. Ltd., I took ownership of screening over 300+ profiles and coordinating 80+ schedules, "
        f"honing my ability to communicate persuasively with diverse professionals and deliver under fast-paced deadlines. "
        f"As a fresher, what sets me apart is not just my academic training, but my relentless drive to master your workflows, take initiative on day one, "
        f"and deliver measurable contributions to {company_name}'s strategic milestones.\n\n"
        f"I welcome the opportunity to discuss how my skill set aligns with your immediate goals for the {job_title} position. "
        f"Thank you for your time, consideration, and consideration of my application.\n\n"
        f"Sincerely,\n\n"
        f"{candidate['full_name']}\n"
        f"{candidate['phone']} | {candidate['email']}\n"
        f"LinkedIn: https://{candidate['linkedin']}"
    )
    
    return letter

def generate_tailored_cold_emails(job_title, company_name, hr_email="", job_desc="", candidate=None):
    if not candidate:
        candidate = DEFAULT_CANDIDATE
        
    track = detect_role_track(job_title, job_desc)
    
    # Email 1: High-converting Value Pitch (Concise, punchy)
    subj_1 = f"Application: {job_title} - Harpartap Singh Randhawa (MBA)"
    body_1 = (
        f"Hi {company_name} Hiring Team,\n\n"
        f"I came across the {job_title} opening at {company_name} and wanted to reach out directly.\n\n"
        f"I recently completed my MBA in Capital Markets (Marketing & Finance) from Panjab University. "
        f"With hands-on experience in corporate screening, pipeline management at Infotechnogen, and practical "
        f"proficiency in advanced Excel and data-driven analysis, I am confident I can contribute immediately to {company_name}'s objectives.\n\n"
        f"I've attached my resume and would welcome a brief 10-minute conversation this week to introduce myself and discuss how I can support your team.\n\n"
        f"Best regards,\n"
        f"{candidate['full_name']}\n"
        f"{candidate['phone']} | {candidate['email']}\n"
        f"LinkedIn: https://{candidate['linkedin']}"
    )

    # Email 2: Problem-Solver / Direct Recruiter Hook
    subj_2 = f"Quick note regarding {company_name}'s {job_title} role"
    body_2 = (
        f"Hello Team,\n\n"
        f"I noticed {company_name} is actively expanding and looking for a {job_title}.\n\n"
        f"As an MBA graduate specializing in Marketing and Finance, I specialize in turning high-level goals into concrete daily execution—whether "
        f"that means building prospect pipelines, running detailed data analyses in Excel/Power BI, or driving stakeholder coordination.\n\n"
        f"Could I share a 2-page project breakdown of how my background aligns with what you need for this role?\n\n"
        f"Thank you for your time!\n\n"
        f"Warmly,\n"
        f"{candidate['full_name']}\n"
        f"{candidate['phone']} | {candidate['email']}"
    )

    # Email 3: LinkedIn InMail / Short Note (under 300 chars)
    body_3 = (
        f"Hi team, I noticed your {job_title} opening at {company_name}. As an MBA graduate in Capital Markets & Marketing with corporate operations experience, "
        f"I'd love to connect and explore how my analytical skills and drive can support your team's goals!"
    )

    return {
        "value_pitch": {"subject": subj_1, "body": body_1},
        "problem_solver": {"subject": subj_2, "body": body_2},
        "linkedin_note": {"subject": f"Connecting regarding {job_title} at {company_name}", "body": body_3}
    }

if __name__ == "__main__":
    res = generate_tailored_resume("Business Development Associate", "TechCorp Global")
    print("Track detected:", res['track'])
    print("Headline:", res['headline'])
    print("\nCover Letter Snippet:")
    print(generate_tailored_cover_letter("Business Development Associate", "TechCorp Global")[:250])
