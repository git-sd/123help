# GhostJob

**Verify before you apply.**

GhostJob checks job offers for scam warning signs. Paste a job link or the offer text, and get a short report that shows what looks suspicious and why.

Built by **Team Who Cares** for the Swim with TinyFish Hackathon.

> GhostJob gives advice, not guarantees. Always verify independently before paying money or sharing documents.

## What it checks

- **Fee demands:** registration fees, deposits, paid training, UPI requests
- **Pressure language:** "guaranteed selection", "urgent", "limited seats"
- **Recruiter email:** public addresses like Gmail, or a domain that doesn't match the company
- **Company:** looks for a possible official careers page for you to check

Each finding gets a label: **Verified**, **Warning**, **Unverified** or **Unknown**. The overall result is **Low**, **Medium** or **High** risk.

## How it works

1. You submit a link or paste the job text.
2. TinyFish fetches the page and searches the web.
3. Gemini analyzes the listing.
4. You get a report with findings, sources and next steps.

If TinyFish or Gemini isn't set up, GhostJob falls back to simple rule-based checks.

## Tech stack

React + Vite, FastAPI, Supabase, TinyFish, Gemini. Hosted on Vercel and Render.

## Run it locally

You need Node.js 20+ and Python 3.12+. No API keys are needed to try it.

**Backend**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

**Frontend** (new terminal, from the repo root)

```bash
npm install
cp .env.example .env
npm run dev
```

Open http://localhost:5173

**Optional:** add `TINYFISH_API_KEY` and `GEMINI_API_KEY` to `backend/.env` for real web checks and AI analysis. Add Supabase keys to save reports to a database.

## Run the tests

```bash
pytest backend/tests -q
```

## Current limits

- Uses public information only.
- A role missing from a careers page is a warning sign, not proof of a scam.
- A convincing copy of a real company can slip through.
- Risk scoring is simple and still being tuned.
- The evidence map is shown as a list, not an interactive graph yet.

## Coming next

Interactive evidence graph, browser extension, reported-domains database, community reporting and multilingual support.

## More docs

See the design documents in this repo (PRD, Architecture, Database, Security, Testing) and [backend/README.md](backend/README.md).

## Team

Team Who Cares: Asheeth, Archit, Shivang and teammates.
