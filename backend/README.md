# GhostJob API

## Local run

```powershell
cd backend
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

The local API exposes `GET /health`, `POST /api/v1/investigations`, and `GET /api/v1/investigations/{id}/report`.
Its current deterministic risk engine detects payment language and pressure language. It intentionally uses an in-memory development store until Supabase credentials are configured.

## Database

Create a Supabase project, then apply [the core migration](../supabase/migrations/0001_ghostjob_core.sql) through the Supabase CLI or SQL editor. It creates the account profile, investigation, source, finding, report and password-reset OTP tables, indexes, and row-level security policies.

## Required production wiring

- Configure Supabase Auth for email/password and its SMTP provider.
- Add the backend's server-only Supabase service-role key to `backend/.env`; never expose it in Vite.
- Implement a Supabase repository to replace the in-memory `reports` dictionary.
- Use a transactional hashed OTP, expiry and single-use consumption flow, or delegate password reset emails to Supabase Auth.
- Add TinyFish/Gemini adapters and a background worker before enabling real investigations.
