# GhostJob – Product Requirements Document (PRD)

*Verify Before You Apply.*

Version 1.0 · Status: Draft · Audience: Founders, developers, designers, testers

## 1. Purpose

GhostJob is an AI-powered web application that investigates job and internship listings and produces an evidence-backed risk report. It helps college students, freshers and job seekers avoid fake jobs, impersonated recruiters and fee-demanding internships before they apply or pay.

This PRD defines what is being built, for whom, and how success is measured. Companion documents cover the Design System, Architecture, Database, Security and Testing.

## 2. Problem Statement

Online recruitment scams are common and increasingly convincing. Applicants, especially students and freshers, face:

- Fake companies advertising attractive roles.
- Recruiters impersonating employees of real organizations.
- Internships demanding registration, processing or security fees.
- Mandatory paid training and payments to "secure selection".
- Unrealistic salary promises and guaranteed-selection claims.
- Listings that cannot be verified through official company sources.

Most applicants lack the time, tools or experience to verify these opportunities themselves. A simple badge ("safe / unsafe") is not enough; users need to see *why* a listing looks risky.

## 3. Goals and Non-Goals

### Goals

1. Let a user submit a job URL or pasted description and receive a risk report in a few minutes.
2. Detect payment requests (registration fees, deposits, paid training) reliably.
3. Verify the company and recruiter against public sources.
4. Explain every finding with evidence and source links.
5. Visualize claims, evidence and verification status in an interactive Scam Evidence Graph.
6. Keep a private history of past investigations per user.

### Non-Goals (v1)

- Guaranteeing that a job is legitimate or fraudulent. The output is advisory only.
- Browser extension, community reporting and multilingual support (future scope).
- Applying to jobs on the user's behalf.
- Collecting or storing sensitive personal data such as ID documents or bank details.

## 4. Target Users and Personas

| Persona | Description | Key Need |
| --- | --- | --- |
| Student Sneha | Final-year college student applying to internships | Know if an internship asking for a fee is a scam |
| Fresher Arjun | Recent graduate applying to many roles via WhatsApp, LinkedIn and job boards | Quickly check unfamiliar recruiters and companies |
| Career Switcher Meera | Experienced professional exploring new roles | Confirm a role exists on the official careers page |
| Admin / Moderator | GhostJob team member | Monitor usage, abuse and system health |

## 5. User Journey

1. **Authentication** – Sign up or log in.
2. **Landing Page** – Introduction to GhostJob and its features, one clear call to action.
3. **User Dashboard** – Overview, start a new investigation, recent reports and statistics.
4. **New Investigation** – Submit a job URL or paste a job description.
5. **Investigation Process** – TinyFish searches websites and collects evidence; progress is shown live.
6. **AI Analysis** – Gemini analyzes the collected information.
7. **Investigation Report** – Risk classification, warning signs and recommendations.
8. **Evidence Graph** – Interactive visualization of claims and supporting evidence.
9. **Investigation History** – Access previously investigated opportunities.

## 6. Functional Requirements

Priority key: **P0** = must have for launch, **P1** = should have, **P2** = nice to have.

### 6.1 Authentication and Accounts

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-A1 | Users can sign up and log in with email and password | P0 |
| FR-A2 | Email verification and password reset | P0 |
| FR-A3 | Optional social login (Google) | P1 |
| FR-A4 | Users can view and delete their account and all associated data | P0 |
| FR-A5 | Role-based access: user and admin | P0 |

### 6.2 Landing Page

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-L1 | Explain what GhostJob does, key features and how it works | P0 |
| FR-L2 | Single primary call to action: "Check a job now" | P0 |
| FR-L3 | Links to Privacy Policy and Terms and Conditions | P0 |
| FR-L4 | Cookie consent banner | P0 |

### 6.3 Dashboard

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-D1 | Prominent "New Investigation" button | P0 |
| FR-D2 | Recent reports list with risk badge, company, role and date | P0 |
| FR-D3 | Statistics: total investigations, count by risk level, fee requests detected | P1 |
| FR-D4 | Empty state for new users with guidance | P1 |

### 6.4 New Investigation (Job Listing Analysis)

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-N1 | Accept a job listing URL or pasted job description | P0 |
| FR-N2 | Validate and sanitize all input; reject unsupported or malicious URLs | P0 |
| FR-N3 | Extract company name, role, salary, recruiter details and application requirements | P0 |
| FR-N4 | Flag potentially suspicious statements (guaranteed selection, urgency, unrealistic pay) | P0 |
| FR-N5 | Optional extra context: recruiter name, email, phone, or company website | P1 |

### 6.5 Internship Fee Detection (Flagship Feature)

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-F1 | Detect requests for registration fees, recruitment or processing fees, security deposits, mandatory paid training, and payments to secure selection | P0 |
| FR-F2 | Show a prominent warning with the exact text that triggered detection | P0 |
| FR-F3 | Recommend independent verification before any payment | P0 |
| FR-F4 | Distinguish genuine paid-course offerings that are clearly labeled optional from mandatory fees (reduce false positives) | P1 |

### 6.6 Company Verification

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-C1 | Find the company's official website | P0 |
| FR-C2 | Find the official careers page | P0 |
| FR-C3 | Check whether the advertised role appears on official sources | P0 |
| FR-C4 | Identify inconsistencies between the listing and company information | P0 |

### 6.7 Recruiter Verification

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-R1 | Examine publicly available recruiter information | P0 |
| FR-R2 | Check email-domain consistency with the company's domain | P0 |
| FR-R3 | Look for public professional profiles | P1 |
| FR-R4 | Identify possible impersonation indicators | P0 |

### 6.8 Investigation Process

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-P1 | Run investigations asynchronously as background jobs | P0 |
| FR-P2 | Show live progress with clear steps (listing read, company check, recruiter check, analysis) | P0 |
| FR-P3 | Handle failures and partial results gracefully with a retry option | P0 |
| FR-P4 | Enforce a maximum investigation time and show a timeout message | P1 |

### 6.9 Risk Assessment Report

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-RP1 | Overall risk level: Low, Medium or High | P0 |
| FR-RP2 | Detected warning signs | P0 |
| FR-RP3 | Verified information | P0 |
| FR-RP4 | Unverified claims | P0 |
| FR-RP5 | Supporting source links | P0 |
| FR-RP6 | Recommended next steps | P0 |
| FR-RP7 | Standing disclaimer that the result is advisory, not a guarantee | P0 |
| FR-RP8 | Export or share report as PDF or private link | P2 |

### 6.10 Scam Evidence Graph

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-G1 | Interactive graph connecting claims, company info, recruiter info, suspicious activities, evidence and verification status | P0 |
| FR-G2 | Each node is classified Verified, Warning, Unverified or Unknown | P0 |
| FR-G3 | Clicking a node shows its evidence and source link | P0 |
| FR-G4 | Legend, zoom, pan and a list-view fallback for accessibility and mobile | P1 |

### 6.11 Investigation History

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-H1 | List all past investigations with search and filter by risk level | P0 |
| FR-H2 | Open any past report and graph | P0 |
| FR-H3 | Delete an investigation | P0 |
| FR-H4 | Re-run an investigation to refresh results | P1 |

### 6.12 Admin

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-AD1 | Protected admin area with usage metrics and investigation counts | P1 |
| FR-AD2 | View system errors, failed jobs and abuse flags | P1 |
| FR-AD3 | Suspend abusive accounts | P1 |

## 7. Risk Classification Rules

| Level | Definition | Typical Triggers |
| --- | --- | --- |
| Low | No major suspicious indicators; available evidence supports the opportunity | Role found on official careers page, consistent recruiter domain, no payment demands |
| Medium | Some warning signs or missing verification; further checking recommended | Role not found on careers page, recruiter unverifiable, vague details |
| High | Strong indicators of potential fraud | Payment demand, impersonation evidence, multiple serious inconsistencies |

Rules:

- Any confirmed mandatory payment demand sets the minimum risk to **High**.
- Missing information alone never produces High; it produces Medium or Unknown.
- Every risk level must list the evidence behind it.
- The report always states that the classification is advisory.

## 8. Non-Functional Requirements

| Area | Requirement |
| --- | --- |
| Performance | Investigation completes in under 2 minutes for 90% of requests; pages load in under 2.5 seconds on a mid-range mobile on 4G |
| Availability | 99% monthly uptime target for the web app and API |
| Scalability | Support concurrent investigations through a job queue with per-user limits |
| Security | Meets the Security document: no secrets in frontend, HTTPS only, rate limiting, input sanitization, access control |
| Privacy | Collect only what is needed; use public information; allow data deletion |
| Accessibility | WCAG 2.1 AA colour contrast, keyboard navigation, alt text, screen-reader labels |
| Responsiveness | Fully usable on mobile, tablet and desktop |
| Reliability | Graceful handling of TinyFish or Gemini failures, with partial reports where possible |
| Observability | Structured logging, error tracking and analytics |

## 9. Success Metrics

| Metric | Target (first 3 months) |
| --- | --- |
| Investigations completed | 1,000+ |
| Report completion rate (started to finished) | 90%+ |
| Fee-detection recall on test set of known fee-demanding listings | 95%+ |
| False-positive rate on a test set of legitimate listings | Under 10% for High risk |
| User-reported helpfulness (thumbs up on reports) | 80%+ |
| Landing page to sign-up conversion | 10%+ |
| Median investigation time | Under 90 seconds |

## 10. Assumptions, Dependencies and Risks

### Dependencies

- TinyFish AI for web investigation.
- Google Gemini API for analysis.
- Supabase for database and authentication.
- Vercel (frontend) and Render (backend) for hosting.

### Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Legitimate jobs missing from careers pages are flagged | False positives, lost trust | Treat as Unverified/Medium, never High on that alone; explain clearly |
| Sophisticated scams imitate real companies | Missed scams | Cross-check email domain, domain age and public warnings; keep disclaimer |
| Third-party API outages or rate limits | Failed investigations | Queue, retries, timeouts, partial reports, caching |
| API cost growth | Budget overrun | Per-user quotas, caching of repeated URLs, input size limits |
| LLM hallucination | Incorrect claims | Require evidence links per finding; separate verified from uncertain; structured output validation |
| Abuse (scraping, spam) | Cost and instability | Rate limiting, CAPTCHA, account verification |
| Legal exposure from labeling a company "scam" | Defamation risk | Neutral wording ("warning signs detected"), evidence-based, advisory disclaimer |

## 11. Release Plan

| Phase | Scope |
| --- | --- |
| Phase 1: Basic Application | React frontend, FastAPI backend, listing input, frontend-backend connection, authentication |
| Phase 2: AI Integration | TinyFish integration, company and recruiter data collection, Gemini analysis |
| Phase 3: Risk Detection and Reporting | Fee detection, risk classification, reports, Scam Evidence Graph, dashboard and history |
| Phase 4: Testing and Deployment | Legit vs suspicious test set, false-positive evaluation, security audit, launch checklist, deployment |

## 12. Pre-Launch Checklist (Last 20 Things)

| # | Item | Owner |
| --- | --- | --- |
| 1 | Privacy policy page | Product / Legal |
| 2 | Terms and conditions page | Product / Legal |
| 3 | Secrets off the frontend | Backend |
| 4 | Force HTTPS | DevOps |
| 5 | Cookie consent banner | Frontend |
| 6 | Meta titles and descriptions | Frontend |
| 7 | Social preview image | Design |
| 8 | Favicon | Design |
| 9 | Sitemap and robots.txt | Frontend |
| 10 | Alt text on images | Frontend |
| 11 | Compress images | Frontend |
| 12 | Check page load speed | Frontend |
| 13 | Fix colour contrast | Design |
| 14 | Make it mobile friendly | Frontend |
| 15 | Custom 404 page | Frontend |
| 16 | Fix broken links | QA |
| 17 | Form validation | Frontend / Backend |
| 18 | Spam protection | Backend |
| 19 | Set up analytics | Frontend |
| 20 | One clear call to action | Design / Product |

Details for each item appear in the Design System, Security and Testing documents.

## 13. Open Questions

1. Free tier limits: how many investigations per user per day or month?
2. Will anonymous (no-login) quick checks be allowed on the landing page?
3. Which job platforms are officially supported in v1 (LinkedIn, Internshala, Naukri, Indeed, WhatsApp text)?
4. Retention period for investigation data and cached web content?
5. Does the team need legal review of the report wording before launch?

## 14. Disclaimer

GhostJob provides advisory risk assessments based on publicly available information. A result does not guarantee that an opportunity is legitimate or fraudulent. Users should always verify independently before applying, sharing personal information or making any payment.
