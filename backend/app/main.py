from uuid import uuid4
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.security import validate_public_url
from app.models.schemas import InvestigationAccepted, InvestigationCreate, Report
from app.services.risk_engine import assess_listing
from supabase import Client, create_client

settings = get_settings()
app = FastAPI(title="GhostJob API", docs_url="/docs" if settings.environment != "production" else None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True, allow_methods=["GET", "POST", "DELETE"], allow_headers=["Authorization", "Content-Type"])

# Development-only in-memory store. Replace with SupabaseRepository in deployment.
reports: dict[str, Report] = {}

def get_supabase() -> Client:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise HTTPException(503, "Database is not configured.")
    return create_client(settings.supabase_url, settings.supabase_service_role_key)

def current_user(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Authentication required.")
    try:
        user = get_supabase().auth.get_user(authorization.removeprefix("Bearer ")).user
        if not user:
            raise ValueError
        return str(user.id)
    except Exception as exc:
        raise HTTPException(401, "Invalid or expired session.") from exc


@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.environment}


@app.post("/api/v1/investigations", response_model=InvestigationAccepted, status_code=status.HTTP_202_ACCEPTED)
def create_investigation(payload: InvestigationCreate, user_id: str = Depends(current_user)):
    if payload.job_url:
        validate_public_url(payload.job_url)
    investigation_id = str(uuid4())
    # The worker will replace this deterministic development result with TinyFish + Gemini evidence.
    report = assess_listing(payload.job_text or "")
    db = get_supabase()
    active = db.table("investigations").select("id", count="exact").eq("user_id", user_id).in_("status", ["queued", "running"]).execute()
    if (active.count or 0) >= settings.max_concurrent_investigations:
        raise HTTPException(429, f"You can run up to {settings.max_concurrent_investigations} investigations at once.")
    db.table("investigations").insert({"id": investigation_id, "user_id": user_id, "input_type": payload.input_type.value,
        "job_url": payload.job_url, "job_text": payload.job_text, "recruiter_name": payload.recruiter.name if payload.recruiter else None,
        "recruiter_email": str(payload.recruiter.email) if payload.recruiter and payload.recruiter.email else None,
        "status": "completed", "risk_level": report.risk_level.value, "risk_score": report.risk_score, "fee_detected": report.fee_detected}).execute()
    db.table("reports").insert({"investigation_id": investigation_id, "summary": report.summary, "next_steps": report.next_steps}).execute()
    if report.findings:
        db.table("findings").insert([{"investigation_id": investigation_id, "category": "payment", "title": finding.title, "detail": finding.detail,
            "quote": finding.quote, "status": finding.status, "severity": 3 if finding.status == "warning" else 1} for finding in report.findings]).execute()
    reports[investigation_id] = report
    return InvestigationAccepted(id=investigation_id)


@app.get("/api/v1/investigations/{investigation_id}/report", response_model=Report)
def get_report(investigation_id: str, user_id: str = Depends(current_user)):
    db = get_supabase()
    row = db.table("investigations").select("risk_level,risk_score,fee_detected,reports(summary,next_steps),findings(title,detail,status,quote)").eq("id", investigation_id).eq("user_id", user_id).execute().data
    if not row:
        raise HTTPException(status_code=404, detail="Investigation not found.")
    data = row[0]; stored = data.get("reports") or {}; stored = stored[0] if isinstance(stored, list) else stored
    return Report(risk_level=data["risk_level"], risk_score=data["risk_score"], fee_detected=data["fee_detected"], summary=stored.get("summary", "Report ready."), next_steps=stored.get("next_steps", []), findings=data.get("findings", []))

@app.get("/api/v1/investigations")
def list_investigations(user_id: str = Depends(current_user)):
    """Newest-first, owner-scoped dashboard history."""
    result = get_supabase().table("investigations").select("id,company_name,job_title,risk_level,status,created_at,fee_detected").eq("user_id", user_id).order("created_at", desc=True).limit(50).execute()
    return {"items": result.data or []}

@app.delete("/api/v1/investigations/{investigation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_investigation(investigation_id: str, user_id: str = Depends(current_user)):
    """Delete only the caller's record; database cascades remove report and findings."""
    result = get_supabase().table("investigations").delete().eq("id", investigation_id).eq("user_id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Investigation not found.")

@app.post("/api/v1/investigations/{investigation_id}/rerun", response_model=InvestigationAccepted, status_code=status.HTTP_202_ACCEPTED)
def rerun_investigation(investigation_id: str, user_id: str = Depends(current_user)):
    source = get_supabase().table("investigations").select("input_type,job_url,job_text,recruiter_name,recruiter_email,recruiter_phone").eq("id", investigation_id).eq("user_id", user_id).execute().data
    if not source:
        raise HTTPException(status_code=404, detail="Investigation not found.")
    row = source[0]
    payload = InvestigationCreate(input_type=row["input_type"], job_url=row.get("job_url"), job_text=row.get("job_text"))
    return create_investigation(payload, user_id)
