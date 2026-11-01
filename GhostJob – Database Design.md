# GhostJob – Database Design

*Verify Before You Apply.*

Version 1.0 · Database: Supabase (PostgreSQL 15+) with Row Level Security · Access: FastAPI (service role) and frontend (anon key, RLS enforced)

## 1. Design Principles

1. **Least data.** Store only what the product needs; use public information; never store ID documents, bank details or passwords (Supabase Auth handles credentials and hashing).
2. **Owner isolation.** Every user-owned row carries `user_id`, and RLS ensures users only see their own data.
3. **Evidence-backed.** Findings, graph nodes and sources all link back to an investigation.
4. **Auditable.** Timestamps on every table; admin actions logged.
5. **Deletable.** Deleting an investigation or account cascades to all related data.
6. **Performant.** Indexes on the access paths used by the dashboard, history and worker queue.

## 2. Entity Overview

```text
auth.users (Supabase)
    |
    +-- profiles (1:1)
    |
    +-- investigations (1:N)
    |       |-- investigation_steps (1:N)
    |       |-- sources (1:N)
    |       |-- findings (1:N)  --< finding_evidence >-- sources
    |       |-- graph_nodes (1:N)
    |       |-- graph_edges (1:N)
    |       |-- reports (1:1)
    |       +-- feedback (1:N)
    |
    +-- usage_quota (1:1)
    +-- consent_records (1:N)

company_cache (shared, no user data)
rate_limit_events (optional, if not using Redis)
audit_log (admin and security events)
```

## 3. Tables

### 3.1 profiles

| Column | Type | Notes |
| --- | --- | --- |
| id | uuid PK | References `auth.users(id)` ON DELETE CASCADE |
| display\_name | text | Optional |
| role | text | `user` (default) or `admin`; only changeable by service role |
| status | text | `active` or `suspended` |
| created\_at | timestamptz | Default `now()` |
| updated\_at | timestamptz | Updated by trigger |

### 3.2 investigations

| Column | Type | Notes |
| --- | --- | --- |
| id | uuid PK | `gen_random_uuid()` |
| user\_id | uuid | FK to profiles, ON DELETE CASCADE, indexed |
| input\_type | text | `url` or `text` |
| job\_url | text | Nullable; normalized and validated |
| job\_url\_hash | text | SHA-256 of normalized URL, used for caching |
| job\_text | text | Nullable; length capped by check constraint |
| recruiter\_name | text | Optional user-provided |
| recruiter\_email | text | Optional user-provided |
| recruiter\_phone | text | Optional user-provided |
| company\_name | text | Extracted |
| job\_title | text | Extracted |
| salary\_text | text | Extracted |
| status | text | `queued`, `running`, `partial`, `completed`, `failed`, `cancelled` |
| current\_step | text | For progress display |
| risk\_level | text | `low`, `medium`, `high`; null until complete |
| risk\_score | int | 0 to 100 |
| fee\_detected | boolean | Flagship flag, default false |
| error\_code | text | User-safe failure reason |
| attempts | int | Worker retry counter |
| locked\_at | timestamptz | Worker lock for the queue |
| started\_at, completed\_at | timestamptz | Timing |
| created\_at, updated\_at | timestamptz | Timestamps |

Constraints: `CHECK (input_type IN ('url','text'))`, `CHECK (char_length(job_text) <= 10000)`, `CHECK (job_url IS NOT NULL OR job_text IS NOT NULL)`.

### 3.3 investigation\_steps

| Column | Type | Notes |
| --- | --- | --- |
| id | uuid PK |  |
| investigation\_id | uuid | FK, cascade |
| step\_key | text | `reading_listing`, `company_check`, `recruiter_check`, `payment_scan`, `analysis`, `report` |
| status | text | `pending`, `running`, `done`, `failed`, `skipped` |
| started\_at, finished\_at | timestamptz |  |
| error\_message | text | Sanitized, no secrets |

### 3.4 sources

Every web page or text excerpt used as evidence.

| Column | Type | Notes |
| --- | --- | --- |
| id | uuid PK |  |
| investigation\_id | uuid | FK, cascade |
| url | text | Public source URL; nullable for pasted text |
| domain | text | Indexed |
| title | text |  |
| source\_type | text | `listing`, `company_site`, `careers_page`, `recruiter_profile`, `scam_report`, `domain_info`, `user_text` |
| excerpt | text | Short relevant excerpt only (not full page), capped length |
| fetched\_at | timestamptz |  |

### 3.5 findings

| Column | Type | Notes |
| --- | --- | --- |
| id | uuid PK |  |
| investigation\_id | uuid | FK, cascade |
| category | text | `payment`, `company`, `recruiter`, `listing_claim`, `consistency`, `scam_report` |
| fee\_type | text | Nullable: `registration`, `processing`, `security_deposit`, `paid_training`, `selection_payment` |
| title | text | Short headline |
| detail | text | Explanation |
| quote | text | Verbatim triggering text, if any |
| status | text | `verified`, `warning`, `unverified`, `unknown` |
| severity | int | 0 to 3, used by the risk engine |
| created\_at | timestamptz |  |

### 3.6 finding\_evidence

| Column | Type | Notes |
| --- | --- | --- |
| finding\_id | uuid | FK to findings, cascade |
| source\_id | uuid | FK to sources, cascade |
| PK | (finding\_id, source\_id) | Composite |

Application rule: a finding with no evidence rows may only have status `unknown`.

### 3.7 graph\_nodes and graph\_edges

| Table | Column | Type | Notes |
| --- | --- | --- | --- |
| graph\_nodes | id | uuid PK |  |
|  | investigation\_id | uuid | FK, cascade |
|  | node\_type | text | `claim`, `company`, `recruiter`, `activity`, `evidence`, `verification` |
|  | label | text | Display text |
|  | status | text | `verified`, `warning`, `unverified`, `unknown` |
|  | finding\_id | uuid | Nullable link to finding |
|  | source\_id | uuid | Nullable link to source |
|  | position\_x, position\_y | real | Optional layout hints |
| graph\_edges | id | uuid PK |  |
|  | investigation\_id | uuid | FK, cascade |
|  | source\_node\_id | uuid | FK to graph\_nodes, cascade |
|  | target\_node\_id | uuid | FK to graph\_nodes, cascade |
|  | relation | text | `supports`, `contradicts`, `not_found`, `derived_from` |

### 3.8 reports

| Column | Type | Notes |
| --- | --- | --- |
| investigation\_id | uuid PK | FK, one report per investigation |
| summary | text | One-paragraph verdict |
| risk\_factors | jsonb | Rules that fired and their weights |
| warning\_signs | jsonb | List of finding IDs |
| verified\_info | jsonb | List of finding IDs |
| unverified\_claims | jsonb | List of finding IDs |
| next\_steps | jsonb | Array of recommended actions |
| model\_name | text | Gemini model used |
| raw\_analysis | jsonb | Validated Gemini JSON (backend access only) |
| disclaimer\_version | text | Which advisory wording was shown |
| created\_at | timestamptz |  |

### 3.9 feedback

| Column | Type | Notes |
| --- | --- | --- |
| id | uuid PK |  |
| investigation\_id | uuid | FK, cascade |
| user\_id | uuid | FK |
| rating | smallint | -1 or 1 |
| comment | text | Optional, length capped |
| created\_at | timestamptz |  |

### 3.10 usage\_quota

| Column | Type | Notes |
| --- | --- | --- |
| user\_id | uuid PK | FK |
| daily\_count | int | Reset daily |
| monthly\_count | int | Reset monthly |
| daily\_limit, monthly\_limit | int | Per-plan limits |
| last\_reset\_day, last\_reset\_month | date |  |

### 3.11 consent\_records

| Column | Type | Notes |
| --- | --- | --- |
| id | uuid PK |  |
| user\_id | uuid | Nullable for anonymous visitors (use a random consent ID) |
| consent\_type | text | `analytics`, `terms`, `privacy` |
| granted | boolean |  |
| policy\_version | text |  |
| created\_at | timestamptz |  |

### 3.12 company\_cache

Shared and contains only public company data, never user data.

| Column | Type | Notes |
| --- | --- | --- |
| domain | text PK | Normalized official domain |
| company\_name | text |  |
| careers\_url | text |  |
| official\_site\_verified | boolean |  |
| data | jsonb | Public findings |
| fetched\_at | timestamptz |  |
| expires\_at | timestamptz | Typically 3 to 7 days |

### 3.13 audit\_log

| Column | Type | Notes |
| --- | --- | --- |
| id | bigserial PK |  |
| actor\_id | uuid | Nullable |
| action | text | `admin_suspend_user`, `account_deleted`, `login_failed_burst`, etc. |
| target\_type, target\_id | text |  |
| metadata | jsonb | No secrets or personal content |
| ip\_hash | text | Hashed, not raw IP |
| created\_at | timestamptz |  |

## 4. SQL Schema (Core Tables)

```sql
create extension if not exists pgcrypto;

create table profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  role text not null default 'user' check (role in ('user','admin')),
  status text not null default 'active' check (status in ('active','suspended')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table investigations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references profiles(id) on delete cascade,
  input_type text not null check (input_type in ('url','text')),
  job_url text,
  job_url_hash text,
  job_text text check (char_length(job_text) <= 10000),
  recruiter_name text,
  recruiter_email text,
  recruiter_phone text,
  company_name text,
  job_title text,
  salary_text text,
  status text not null default 'queued'
    check (status in ('queued','running','partial','completed','failed','cancelled')),
  current_step text,
  risk_level text check (risk_level in ('low','medium','high')),
  risk_score int check (risk_score between 0 and 100),
  fee_detected boolean not null default false,
  error_code text,
  attempts int not null default 0,
  locked_at timestamptz,
  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (job_url is not null or job_text is not null)
);

create table sources (
  id uuid primary key default gen_random_uuid(),
  investigation_id uuid not null references investigations(id) on delete cascade,
  url text,
  domain text,
  title text,
  source_type text not null,
  excerpt text check (char_length(excerpt) <= 2000),
  fetched_at timestamptz not null default now()
);

create table findings (
  id uuid primary key default gen_random_uuid(),
  investigation_id uuid not null references investigations(id) on delete cascade,
  category text not null,
  fee_type text,
  title text not null,
  detail text,
  quote text,
  status text not null check (status in ('verified','warning','unverified','unknown')),
  severity int not null default 0 check (severity between 0 and 3),
  created_at timestamptz not null default now()
);

create table finding_evidence (
  finding_id uuid references findings(id) on delete cascade,
  source_id uuid references sources(id) on delete cascade,
  primary key (finding_id, source_id)
);

create table graph_nodes (
  id uuid primary key default gen_random_uuid(),
  investigation_id uuid not null references investigations(id) on delete cascade,
  node_type text not null
    check (node_type in ('claim','company','recruiter','activity','evidence','verification')),
  label text not null,
  status text not null check (status in ('verified','warning','unverified','unknown')),
  finding_id uuid references findings(id) on delete set null,
  source_id uuid references sources(id) on delete set null
);

create table graph_edges (
  id uuid primary key default gen_random_uuid(),
  investigation_id uuid not null references investigations(id) on delete cascade,
  source_node_id uuid not null references graph_nodes(id) on delete cascade,
  target_node_id uuid not null references graph_nodes(id) on delete cascade,
  relation text not null check (relation in ('supports','contradicts','not_found','derived_from'))
);
```

## 5. Indexes

| Index | Purpose |
| --- | --- |
| `investigations (user_id, created_at desc)` | Dashboard recent reports and history list |
| `investigations (user_id, risk_level)` | History filter by risk |
| `investigations (status, created_at) where status = 'queued'` | Worker queue polling |
| `investigations (job_url_hash, created_at desc)` | Cache lookup for repeated URLs |
| `sources (investigation_id)`, `findings (investigation_id)`, `graph_nodes (investigation_id)`, `graph_edges (investigation_id)` | Report and graph loading |
| `sources (domain)` | Domain-level analysis |
| `company_cache (expires_at)` | Cache cleanup |
| `audit_log (actor_id, created_at desc)` | Admin review |

## 6. Worker Queue Query

```sql
update investigations
set status = 'running', locked_at = now(), attempts = attempts + 1,
    started_at = coalesce(started_at, now())
where id = (
  select id from investigations
  where status = 'queued'
  order by created_at
  for update skip locked
  limit 1
)
returning *;
```

A sweeper marks rows with `status = 'running'` and `locked_at` older than the timeout as `failed`.

## 7. Row Level Security

Enable RLS on **every** table in the public schema. The service role used by the backend bypasses RLS, so the API must also check ownership. RLS protects direct client access with the anon key.

```sql
alter table profiles enable row level security;
alter table investigations enable row level security;
alter table sources enable row level security;
alter table findings enable row level security;
alter table finding_evidence enable row level security;
alter table graph_nodes enable row level security;
alter table graph_edges enable row level security;
alter table reports enable row level security;
alter table feedback enable row level security;
alter table usage_quota enable row level security;
alter table consent_records enable row level security;
alter table audit_log enable row level security;   -- no policies: service role only

-- Profiles: read own, update limited fields (not role or status)
create policy "profiles_select_own" on profiles for select using (auth.uid() = id);
create policy "profiles_update_own" on profiles for update
  using (auth.uid() = id) with check (auth.uid() = id);

-- Investigations: owner can read and delete; inserts and updates go through the API
create policy "inv_select_own" on investigations for select using (auth.uid() = user_id);
create policy "inv_delete_own" on investigations for delete using (auth.uid() = user_id);

-- Child tables: access only through ownership of the parent investigation
create policy "findings_select_own" on findings for select using (
  exists (select 1 from investigations i
          where i.id = findings.investigation_id and i.user_id = auth.uid()));
-- repeat the same pattern for sources, graph_nodes, graph_edges, reports, finding_evidence

-- Feedback: owner can insert and read own
create policy "feedback_insert_own" on feedback for insert with check (auth.uid() = user_id);
create policy "feedback_select_own" on feedback for select using (auth.uid() = user_id);
```

RLS rules of thumb:

- Users **cannot** insert or update `investigations`, `findings`, `reports` or `usage_quota` directly; only the backend does, so risk results cannot be tampered with.
- A column-level guard (trigger) prevents users from changing `profiles.role` or `status`.
- `company_cache` and `audit_log` have no client policies (service role only).
- Test RLS with two users to confirm that one cannot read the other's data.

## 8. Triggers and Functions

| Name | Purpose |
| --- | --- |
| `set_updated_at()` | Updates `updated_at` on row change |
| `handle_new_user()` | Creates `profiles` and `usage_quota` rows when a new auth user signs up |
| `prevent_role_change()` | Blocks non-service updates to `profiles.role` and `status` |
| `purge_expired_cache()` | Scheduled job removing expired `company_cache` rows |

## 9. Data Lifecycle and Privacy

| Data | Retention | Deletion |
| --- | --- | --- |
| Investigations, findings, sources, reports | Until the user deletes them, or 12 months of inactivity (configurable) | Cascade on delete |
| Account data | Until account deletion | `DELETE /me` removes auth user and cascades |
| Pasted job text and recruiter details | With the investigation | Deleted with investigation; consider redacting phone and email after 90 days |
| Company cache | 3 to 7 days | Scheduled purge |
| Audit log | 12 months | Scheduled purge; IPs stored hashed |
| Consent records | While account exists, or 3 years for anonymous | Purge schedule |

Privacy notes:

- Recruiter name, email and phone are personal data; store only if provided, show only to the owner, and never expose in shared caches.
- Do not store full web page HTML; store short excerpts and URLs.
- Provide data export and deletion to meet privacy-policy promises.

## 10. Security Controls for the Database

- RLS on all tables; no table left open to the anon role.
- Service role key only on the backend and worker; never in the frontend or git.
- Parameterised queries only (no string-built SQL).
- Separate Supabase projects for dev, staging and production.
- Enforce TLS connections; restrict direct database access and rotate credentials.
- Enable automated daily backups and test restoring them.
- Least-privilege database roles; revoke default public privileges.
- Monitor slow queries and failed auth attempts.

## 11. Migrations and Seeding

| Practice | Detail |
| --- | --- |
| Migration tool | Supabase CLI migrations (`supabase/migrations/*.sql`) committed to git |
| Review | Every migration reviewed in a pull request |
| Seed data | Synthetic test users and a labelled set of legitimate and suspicious sample listings for testing (no real personal data) |
| Rollback | Each migration has a documented rollback or is backwards compatible |

## 12. Dashboard Statistics Queries

```sql
-- Total and by risk level for the signed-in user (run through the API)
select risk_level, count(*) from investigations
where user_id = :uid and status in ('completed','partial')
group by risk_level;

-- Fee requests detected
select count(*) from investigations where user_id = :uid and fee_detected;
```
