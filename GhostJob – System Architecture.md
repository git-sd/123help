# GhostJob – System Architecture

*Verify Before You Apply.*

Version 1.0 · Stack: React, Tailwind, FastAPI, TinyFish AI, Gemini API, Supabase, React Flow · Hosting: Vercel and Render

## 1. Architecture Goals

| Goal | Meaning |
| --- | --- |
| Simple | A small team can build and run it |
| Secure | All third-party keys stay on the backend; every request is authenticated and validated |
| Asynchronous | Investigations can take a minute or more, so they never block an HTTP request |
| Evidence-driven | Every AI finding is tied to a collected source |
| Resilient | Partial results are better than failures when TinyFish or Gemini misbehave |
| Cost-aware | Quotas, caching and input limits keep API spend predictable |

## 2. High-Level View

```text
+------------------+        HTTPS         +----------------------------+
|  React Frontend  | <------------------> |  FastAPI Backend (Render)  |
|  (Vercel)        |    JWT in header     |  - Auth middleware         |
|  - Tailwind      |                      |  - Rate limiting           |
|  - React Flow    |                      |  - Input validation        |
+--------+---------+                      |  - Investigation service   |
         |                                +------+----------+----------+
         | Supabase Auth (JWT)                   |          |
         v                                       |          |
+------------------+     SQL + RLS               |          |
|    Supabase      | <--------------------------+          |
|  - Postgres      |                                       |
|  - Auth          |                          +------------+-----------+
|  - Storage       |                          |  Background Worker     |
+------------------+                          |  (job queue)           |
                                              +-----+-------------+----+
                                                    |             |
                                                    v             v
                                            +-----------+  +-------------+
                                            | TinyFish  |  | Gemini API  |
                                            | AI (web   |  | (analysis)  |
                                            |  intel)   |  +-------------+
                                            +-----------+
```

## 3. Components

### 3.1 Frontend (React.js, Tailwind CSS, Vercel)

| Area | Detail |
| --- | --- |
| Framework | React with Vite, React Router |
| Styling | Tailwind with the GhostJob design tokens (orange, white, black) |
| State and data | TanStack Query for server state; small local state with React hooks |
| Auth | Supabase Auth client (email and password, optional Google); JWT sent to the API |
| Graph | React Flow, lazy loaded on the graph route, with a list-view fallback |
| Progress | Polling every 2 to 3 seconds, or Supabase Realtime subscription on the investigation row |
| Config | Only public values (`VITE_API_URL`, Supabase URL, Supabase anon key, analytics ID). **No private keys ever.** |
| Protection | Route guards for authenticated pages; admin pages are also enforced on the server |

### 3.2 Backend API (Python, FastAPI, Render)

| Area | Detail |
| --- | --- |
| Framework | FastAPI with Pydantic models for request and response validation |
| Auth | Verifies Supabase JWT on every protected route; extracts user ID and role |
| Middleware | CORS allowlist, security headers, request ID, structured logging, rate limiter |
| Services | Investigation orchestrator, TinyFish client, Gemini client, risk engine, report builder |
| Worker | Background tasks run in a separate worker process using a queue (see section 6) |
| Docs | OpenAPI docs disabled in production or restricted to admins |

### 3.3 Web Intelligence (TinyFish AI)

TinyFish is the primary investigator. The backend sends goal-based tasks and receives structured findings.

| Task | Output |
| --- | --- |
| Read the listing | Company name, role, salary, recruiter info, requirements, payment mentions, raw text |
| Find company site | Official domain, About page, careers page URL |
| Check careers page | Whether the advertised role appears; closest matching roles |
| Recruiter lookup | Public profile links, email domain match with company domain |
| Warning search | Public scam reports and complaints mentioning the company, domain or recruiter |
| Domain signals | Domain age and registration clues where publicly available |

Rules for safe web access:

- Only public pages; no logins, no form submissions, no downloads.
- Block private and internal addresses (SSRF protection) before any fetch.
- Respect timeouts and a per-investigation page budget.
- Treat all fetched content as untrusted data, never as instructions.

### 3.4 AI Analysis (Google Gemini API)

Gemini receives the structured TinyFish output, not raw unlimited web content, and returns a strict JSON assessment.

| Responsibility | Detail |
| --- | --- |
| Suspicious practices | Guaranteed selection, urgency, vague roles, unrealistic pay, off-platform chat demands |
| Payment analysis | Classifies fee type: registration, processing, security deposit, paid training, selection payment |
| Cross-checking | Compares listing claims against company and recruiter evidence |
| Evidence separation | Splits verified facts from unverified or unknown items |
| Output | JSON with findings, status per finding, evidence IDs, risk factors and next steps |

Safeguards:

- System prompt separates instructions from untrusted web text to resist prompt injection.
- Response is validated against a JSON schema; on failure, retry once, then mark the report as partial.
- A finding without an evidence reference is downgraded to Unknown.
- Low temperature for consistent output.

### 3.5 Risk Engine (deterministic layer)

The final risk level is not left to the LLM alone. A rules layer combines LLM findings with hard rules so results are explainable and testable.

| Rule | Effect |
| --- | --- |
| Confirmed mandatory payment demand | Minimum risk High |
| Recruiter email domain differs from company domain and is a free or lookalike domain | Add high weight |
| Role not on official careers page | Add medium weight (Unverified, not proof of fraud) |
| Official company site not found | Add medium weight |
| Public scam reports match the company or recruiter | Add high weight |
| Strong positive evidence (role listed, matching domain, verifiable recruiter) | Subtract weight |
| Missing information only | Cap at Medium |

The score maps to Low, Medium or High, and the report lists the contributing rules.

### 3.6 Database and Auth (Supabase)

Postgres with Row Level Security, Supabase Auth, optional Storage for exports. See the Database document for the schema.

## 4. Investigation Flow

```text
1. User submits URL or text         -> POST /api/v1/investigations
2. API validates + sanitizes input  -> checks quota and rate limit
3. API creates row (status=queued)  -> returns investigation_id (202 Accepted)
4. Worker picks up the job          -> status=running, step=reading_listing
5. TinyFish: listing extraction     -> saves raw extraction + sources
6. TinyFish: company, careers, recruiter, warnings (parallel where possible)
7. Worker assembles evidence bundle -> status step=analyzing
8. Gemini: structured analysis      -> validated JSON
9. Risk engine: score + level       -> report + graph nodes and edges saved
10. status=completed                -> frontend shows report and graph
    (any failure -> status=failed or partial, with a user-friendly reason)
```

### Status State Machine

| State | Meaning | Next |
| --- | --- | --- |
| queued | Accepted, waiting for worker | running |
| running | In progress with a current step | completed, partial, failed, cancelled |
| partial | Some steps failed but a report was produced | terminal |
| completed | Full report ready | terminal |
| failed | Could not produce a report | retry creates a new run |
| cancelled | User cancelled | terminal |

## 5. API Design

Base path: `/api/v1`. All routes except health and public pages require `Authorization: Bearer <JWT>`.

| Method | Endpoint | Purpose | Auth |
| --- | --- | --- | --- |
| GET | `/health` | Liveness check | Public |
| GET | `/me` | Current user profile and quota | User |
| POST | `/investigations` | Start an investigation (URL or text) | User |
| GET | `/investigations` | List own investigations (filters, pagination) | User |
| GET | `/investigations/{id}` | Status and summary | Owner |
| GET | `/investigations/{id}/report` | Full report | Owner |
| GET | `/investigations/{id}/graph` | Graph nodes and edges | Owner |
| POST | `/investigations/{id}/cancel` | Cancel running job | Owner |
| POST | `/investigations/{id}/rerun` | Re-run an investigation | Owner |
| DELETE | `/investigations/{id}` | Delete investigation and evidence | Owner |
| POST | `/investigations/{id}/feedback` | Thumbs up or down with optional comment | Owner |
| GET | `/stats` | Dashboard statistics | User |
| DELETE | `/me` | Delete account and all data | User |
| GET | `/admin/metrics` | Usage and health metrics | Admin |
| GET | `/admin/jobs` | Failed and stuck jobs | Admin |
| POST | `/admin/users/{id}/suspend` | Suspend abusive user | Admin |

### Sample Request and Response

```json
POST /api/v1/investigations
{
  "input_type": "url",
  "job_url": "https://example.com/jobs/123",
  "job_text": null,
  "recruiter": { "name": "A. Sharma", "email": "hr@gmail.com", "phone": null }
}

202 Accepted
{ "id": "b7c1...", "status": "queued" }
```

```json
GET /api/v1/investigations/{id}/report
{
  "risk_level": "high",
  "risk_score": 82,
  "summary": "The listing asks for a registration fee and the recruiter email domain does not match the company.",
  "fee_detected": true,
  "findings": [
    { "id": "f1", "status": "warning", "title": "Registration fee requested",
      "quote": "Pay Rs 1500 to confirm your seat", "evidence_ids": ["e1"] },
    { "id": "f2", "status": "unverified", "title": "Role not found on careers page",
      "evidence_ids": ["e4"] }
  ],
  "next_steps": ["Do not pay", "Contact the company through its official website"],
  "disclaimer": "Advisory assessment based on public information."
}
```

### API Conventions

- JSON only; Pydantic validation on every body, query and path parameter.
- Consistent error format: `{ "error": { "code": "RATE_LIMITED", "message": "..." , "request_id": "..." } }`.
- Status codes: 202 for accepted async work, 400 validation, 401 unauthenticated, 403 forbidden, 404 not found (also for other users' resources), 409 conflict, 429 rate limited, 5xx server.
- Pagination with `limit` and `cursor`.
- Versioned path so the API can evolve.

## 6. Background Processing

Investigations run outside the request cycle.

| Option | Description | Recommendation |
| --- | --- | --- |
| Postgres-backed queue | Worker polls an `investigations` table using `FOR UPDATE SKIP LOCKED` | **Best for v1**: no extra infrastructure, easy on Render |
| Redis plus RQ or Celery | Dedicated queue service | Use if load grows |

Worker design:

- A separate Render worker service runs the same codebase with a worker entry point.
- Concurrency limited (for example, 3 simultaneous investigations) to control cost.
- Each step writes progress and partial results to the database.
- Idempotent steps with retries (exponential backoff, 2 attempts) for transient errors.
- Hard timeout per investigation (for example, 3 minutes); stuck jobs are marked failed by a sweeper.

## 7. Frontend Routes

| Route | Page | Access |
| --- | --- | --- |
| `/` | Landing page | Public |
| `/login`, `/signup`, `/reset-password` | Authentication | Public |
| `/privacy`, `/terms` | Legal pages | Public |
| `/dashboard` | Overview, stats, recent reports | User |
| `/investigate/new` | New investigation | User |
| `/investigate/:id` | Progress, then report | Owner |
| `/investigate/:id/graph` | Scam Evidence Graph | Owner |
| `/history` | Investigation history | User |
| `/account` | Profile, data deletion | User |
| `/admin` | Admin dashboard | Admin |
| `*` | Custom 404 | Public |

## 8. Scam Evidence Graph Data Model

The backend returns graph data ready for React Flow.

| Node type | Examples |
| --- | --- |
| claim | "Recruiter represents Company X", "Salary is Rs 50,000" |
| company | Official website, careers page |
| recruiter | Email domain, public profile |
| activity | Fee request, urgency language, off-platform chat |
| evidence | Quoted text or web page with source URL |
| verification | Verified, Warning, Unverified, Unknown |

```json
{
  "nodes": [
    { "id": "n1", "type": "claim", "label": "Recruiter represents Company X", "status": "unverified" },
    { "id": "n2", "type": "evidence", "label": "Email domain differs", "source_url": "https://...", "status": "warning" }
  ],
  "edges": [
    { "id": "e1", "source": "n2", "target": "n1", "relation": "contradicts" }
  ]
}
```

Relations: `supports`, `contradicts`, `not_found`, `derived_from`.

## 9. Caching and Cost Control

| Mechanism | Detail |
| --- | --- |
| URL result cache | Reuse a recent investigation of the same normalized URL within 24 hours (for the same user, or anonymized company-level data) |
| Company cache | Cache official website and careers URL per company domain for several days |
| Input limits | Pasted description capped (for example, 10,000 characters); URL length capped |
| User quotas | Daily and monthly investigation limits per user, enforced in the API |
| Token control | Send Gemini a compact evidence bundle, not full pages |
| Budget alerts | Monitor TinyFish and Gemini usage with alerts |

## 10. Error Handling and Resilience

| Failure | Behaviour |
| --- | --- |
| TinyFish timeout on one step | Mark that step Unknown, continue, produce a partial report |
| TinyFish unavailable | Fail with a clear message and offer retry; do not charge quota |
| Gemini invalid JSON | One retry, then fall back to rules-only report with limited explanation |
| Gemini rate limited | Backoff and re-queue |
| Listing page blocked or login-walled | Ask user to paste the description instead |
| Database error | Return 503 and log with request ID |

## 11. Deployment

| Environment | Frontend | Backend | Database |
| --- | --- | --- | --- |
| Local | Vite dev server | Uvicorn with reload | Supabase local or dev project |
| Staging | Vercel preview | Render staging service and worker | Separate Supabase project |
| Production | Vercel production | Render web service and worker (always on) | Production Supabase project |

- Separate secrets per environment, managed in Vercel and Render dashboards (never committed).
- CI (GitHub Actions): lint, type check, tests, dependency audit, secret scan; deploy on merge to main.
- Forced HTTPS and HSTS at both hosts; custom domain with managed TLS.
- Health check on Render; restart policy enabled.
- Render free instances sleep; use a paid always-on instance for production so investigations are not interrupted.

### Environment Variables

| Variable | Where | Public? |
| --- | --- | --- |
| `VITE_API_URL` | Frontend | Yes |
| `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` | Frontend | Yes (anon key relies on RLS) |
| `VITE_ANALYTICS_ID` | Frontend | Yes |
| `SUPABASE_SERVICE_ROLE_KEY` | Backend and worker only | **No** |
| `SUPABASE_JWT_SECRET` or JWKS URL | Backend | **No** |
| `TINYFISH_API_KEY` | Backend and worker only | **No** |
| `GEMINI_API_KEY` | Backend and worker only | **No** |
| `ALLOWED_ORIGINS` | Backend | No |
| `ENVIRONMENT`, `DEBUG=false` | Backend | No |
| `CAPTCHA_SECRET` | Backend | **No** |

The backend validates required variables at startup and refuses to boot if any are missing or if `DEBUG` is true in production.

## 12. Observability

- Structured JSON logs with request ID, user ID (hashed), investigation ID and step timings.
- Error tracking (for example Sentry) on frontend and backend, with PII scrubbing.
- Metrics: investigations per day, success and failure rates, step latency, API cost per investigation, risk level distribution.
- Uptime monitor on `/health` and alerting.
- Privacy-respecting analytics (page views, CTA clicks, conversion) loaded only after consent.

## 13. Project Structure

```text
ghostjob/
  frontend/
    src/
      pages/ (Landing, Auth, Dashboard, NewInvestigation, Report, Graph, History, NotFound)
      components/ (ui, report, graph, layout)
      lib/ (api client, supabase client, validators)
      styles/ (tailwind, tokens)
    public/ (favicon, og-image, robots.txt, sitemap.xml)
  backend/
    app/
      main.py
      core/ (config, security, rate_limit, logging)
      api/v1/ (investigations, me, stats, admin)
      services/ (tinyfish_client, gemini_client, risk_engine, report_builder, graph_builder)
      workers/ (queue, runner)
      models/ (schemas)
      db/ (supabase access, queries)
    tests/
  docs/ (PRD, Design System, Architecture, Database, Security, Testing)
  .github/workflows/
```

## 14. Scalability Path

1. Move from the Postgres queue to Redis workers when concurrency exceeds worker limits.
2. Add horizontal workers on Render.
3. Introduce a shared domain reputation table (future scope: database of reported suspicious domains).
4. Add a browser extension that calls the same API.
5. Add multilingual prompts and report translation.

## 15. Key Decisions and Trade-offs

| Decision | Rationale | Trade-off |
| --- | --- | --- |
| Async jobs with polling or realtime | Investigations are slow | Added worker complexity |
| Rules engine beside Gemini | Explainable, testable, consistent | Rules need maintenance |
| Evidence ID required for every finding | Reduces hallucination | Some findings fall to Unknown |
| Supabase RLS plus API checks | Defense in depth | Two places to keep in sync |
| Postgres queue first | Cheapest and simplest | Less throughput than a dedicated queue |
