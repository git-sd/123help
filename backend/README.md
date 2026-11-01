# GhostJob API

## Local run

```powershell
cd backend
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

The local API exposes `GET /health`, `GET /health/providers`, `POST /api/v1/investigations`, and `GET /api/v1/investigations/{id}/report`.
Its current deterministic risk engine detects payment language and pressure language. It intentionally uses an in-memory development store until Supabase credentials are configured.

## Connect TinyFish and Gemini

Copy `.env.example` to `.env`, then set the server-only keys:

```bash
TINYFISH_API_KEY=...
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.0-flash
```

Restart the API and confirm configuration without exposing secrets:

```bash
curl http://localhost:8000/health/providers
```

Run a live, secret-safe provider check from `backend/`:

```bash
python scripts/provider_smoke.py
```

It reports `PASS`, `SKIP`, or `FAIL` for each provider and never prints keys or response bodies.

With keys configured, TinyFish handles rendered listing fetches and careers search, while Gemini performs structured risk analysis. If either provider is unavailable, the worker falls back to direct fetch and deterministic rules.

## Database

Create a Supabase project, then apply [the core migration](../supabase/migrations/0001_ghostjob_core.sql) through the Supabase CLI or SQL editor. It creates the account profile, investigation, source, finding, report and password-reset OTP tables, indexes, and row-level security policies.

## Required production wiring

- Configure Supabase Auth for email/password and its SMTP provider.
- Add the backend's server-only Supabase service-role key to `backend/.env`; never expose it in Vite.
- Implement a Supabase repository to replace the in-memory `reports` dictionary.
- Use a transactional hashed OTP, expiry and single-use consumption flow, or delegate password reset emails to Supabase Auth.
- Add production queue persistence and provider smoke tests before launch.
