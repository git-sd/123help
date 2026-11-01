from datetime import datetime, timezone
from uuid import uuid4
from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.security import validate_public_url
from app.models.schemas import Finding, InvestigationAccepted, InvestigationCreate, Report, RiskLevel, Source
from app.services.graph_builder import build_graph
from app.services.listing_fetcher import fetch_listing
from app.services.analysis_provider import analyze_listing
from app.services.web_verifier import verify_listing
from supabase import Client, create_client

settings = get_settings()
app = FastAPI(title="GhostJob API", docs_url="/docs" if settings.environment != "production" else None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True, allow_methods=["GET", "POST", "DELETE"], allow_headers=["Authorization", "Content-Type"])

# Development-only in-memory store. Replace with SupabaseRepository in deployment.
reports: dict[str, Report] = {}
investigations: dict[str, dict] = {}


def database_configured() -> bool:
    return bool(settings.supabase_url and settings.supabase_service_role_key and not settings.supabase_service_role_key.startswith("replace-"))

def get_supabase() -> Client:
    if not database_configured():
        raise HTTPException(503, "Database is not configured.")
    return create_client(settings.supabase_url, settings.supabase_service_role_key)

def current_user(authorization: str | None = Header(default=None)) -> str:
    # Local development is intentionally usable without external credentials.
    # This branch is never enabled when a real service-role key is configured.
    if not database_configured() and settings.environment != "production":
        return "local-dev-user"
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
    return {"status": "ok", "environment": settings.environment, "database": "supabase" if database_configured() else "memory",
            "analysis_provider": "gemini+rules" if settings.gemini_api_key and not settings.gemini_api_key.startswith("replace-") else "rules",
            "web_provider": "tinyfish+direct" if settings.tinyfish_api_key and not settings.tinyfish_api_key.startswith("replace-") else "direct"}


@app.get("/health/providers")
def provider_health():
    """Safe provider readiness information; never returns API keys."""
    gemini_configured = bool(settings.gemini_api_key and not settings.gemini_api_key.startswith("replace-"))
    tinyfish_configured = bool(settings.tinyfish_api_key and not settings.tinyfish_api_key.startswith("replace-"))
    return {
        "gemini": {"configured": gemini_configured, "model": settings.gemini_model,
                   "endpoint": "https://generativelanguage.googleapis.com/v1beta/{model}:generateContent"},
        "tinyfish": {"configured": tinyfish_configured, "fetch_endpoint": settings.tinyfish_fetch_url,
                     "search_endpoint": "https://api.search.tinyfish.ai"},
        "fallbacks": {"analysis": "rules", "web": "direct_fetch"},
    }


async def process_investigation(investigation_id: str, payload: InvestigationCreate) -> None:
    """Run one investigation outside the request/response path."""
    record = investigations.get(investigation_id)
    if record:
        record["status"] = "running"
    try:
        listing_text = payload.job_text or ""
        source_url = payload.job_url
        if payload.job_url:
            listing_text, source_url = await fetch_listing(payload.job_url)
        sources = [Source(url=source_url)] if source_url else []
        report = await analyze_listing(listing_text, sources)
        entities, verification_findings, verification_sources = await verify_listing(listing_text, source_url)
        report.findings.extend(verification_findings)
        report.sources.extend(source for source in verification_sources if source.url not in {item.url for item in report.sources})
        report.graph = build_graph(entities.get("company_name"), entities.get("job_title"), entities.get("recruiter_email"), report.findings, report.sources)
        if verification_findings and report.risk_level == "low":
            report.risk_level = RiskLevel.medium
            report.risk_score = max(report.risk_score, 42)
            report.next_steps.insert(0, "Verify the recruiter and company through an official website before sharing documents.")
        record = investigations.get(investigation_id)
        if record:
            record.update({"status": "completed", "risk_level": report.risk_level.value, "risk_score": report.risk_score, "fee_detected": report.fee_detected,
                           "company_name": entities.get("company_name"), "job_title": entities.get("job_title")})
        if database_configured():
            db = get_supabase()
            db.table("investigations").update({"status": "completed", "risk_level": report.risk_level.value, "risk_score": report.risk_score, "fee_detected": report.fee_detected,
                                                "company_name": entities.get("company_name"), "job_title": entities.get("job_title")}).eq("id", investigation_id).execute()
            db.table("reports").insert({"investigation_id": investigation_id, "summary": report.summary, "next_steps": report.next_steps}).execute()
            if source_url:
                db.table("sources").insert({"investigation_id": investigation_id, "url": source_url, "title": "Job listing", "source_type": "job_listing"}).execute()
            if verification_sources:
                db.table("sources").insert([{"investigation_id": investigation_id, "url": source.url, "title": source.title, "source_type": source.source_type} for source in verification_sources]).execute()
            if report.findings:
                db.table("findings").insert([{"investigation_id": investigation_id, "category": "payment" if any(word in finding.title.lower() for word in ("payment", "fee")) else "verification", "title": finding.title, "detail": finding.detail,
                    "quote": finding.quote, "status": finding.status, "severity": 3 if finding.status == "warning" else 1} for finding in report.findings]).execute()
        reports[investigation_id] = report
    except Exception as exc:
        if record:
            record.update({"status": "failed", "error_code": "listing_unavailable" if isinstance(exc, HTTPException) else "worker_error"})
        if database_configured():
            get_supabase().table("investigations").update({"status": "failed", "error_code": "listing_unavailable" if isinstance(exc, HTTPException) else "worker_error"}).eq("id", investigation_id).execute()


@app.post("/api/v1/investigations", response_model=InvestigationAccepted, status_code=status.HTTP_202_ACCEPTED)
async def create_investigation(payload: InvestigationCreate, background_tasks: BackgroundTasks | None = None, user_id: str = Depends(current_user)):
    if payload.job_url:
        validate_public_url(payload.job_url)
    investigation_id = str(uuid4())
    active_count = sum(1 for item in investigations.values() if item["user_id"] == user_id and item["status"] in {"queued", "running"})
    if database_configured():
        db = get_supabase()
        active = db.table("investigations").select("id", count="exact").eq("user_id", user_id).in_("status", ["queued", "running"]).execute()
        active_count = active.count or 0
    if active_count >= settings.max_concurrent_investigations:
        raise HTTPException(429, f"You can run up to {settings.max_concurrent_investigations} investigations at once.")
    record = {"id": investigation_id, "user_id": user_id, "input_type": payload.input_type.value,
        "job_url": payload.job_url, "job_text": payload.job_text, "recruiter_name": payload.recruiter.name if payload.recruiter else None,
        "recruiter_email": str(payload.recruiter.email) if payload.recruiter and payload.recruiter.email else None,
        "status": "queued", "risk_level": None, "risk_score": None, "fee_detected": False,
        "company_name": None, "job_title": None, "created_at": datetime.now(timezone.utc).isoformat()}
    investigations[investigation_id] = record
    if database_configured():
        db = get_supabase()
        db.table("investigations").insert(record).execute()
    if background_tasks is not None:
        background_tasks.add_task(process_investigation, investigation_id, payload)
    else:
        await process_investigation(investigation_id, payload)
    return InvestigationAccepted(id=investigation_id, status="queued")


@app.get("/api/v1/investigations/{investigation_id}/status")
def get_investigation(investigation_id: str, user_id: str = Depends(current_user)):
    if not database_configured():
        item = investigations.get(investigation_id)
        if not item or item["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="Investigation not found.")
        return item
    rows = get_supabase().table("investigations").select("id,status,risk_level,risk_score,fee_detected,error_code,created_at,updated_at").eq("id", investigation_id).eq("user_id", user_id).execute().data
    if not rows:
        raise HTTPException(status_code=404, detail="Investigation not found.")
    return rows[0]


@app.get("/api/v1/investigations/{investigation_id}/report", response_model=Report)
def get_report(investigation_id: str, user_id: str = Depends(current_user)):
    if not database_configured():
        if investigation_id not in investigations or investigations[investigation_id]["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="Investigation not found.")
        if investigation_id not in reports:
            raise HTTPException(status_code=409, detail="Investigation is still in progress.")
        return reports[investigation_id]
    db = get_supabase()
    row = db.table("investigations").select("risk_level,risk_score,fee_detected,company_name,job_title,recruiter_email,reports(summary,next_steps),findings(title,detail,status,quote),sources(url,title,source_type)").eq("id", investigation_id).eq("user_id", user_id).execute().data
    if not row:
        raise HTTPException(status_code=404, detail="Investigation not found.")
    data = row[0]; stored = data.get("reports") or {}; stored = stored[0] if isinstance(stored, list) else stored
    sources = data.get("sources", [])
    findings = data.get("findings", [])
    graph = build_graph(data.get("company_name"), data.get("job_title"), data.get("recruiter_email"), [Finding(**item) for item in findings], [Source(**item) for item in sources])
    return Report(risk_level=data["risk_level"], risk_score=data["risk_score"], fee_detected=data["fee_detected"], summary=stored.get("summary", "Report ready."), next_steps=stored.get("next_steps", []), findings=findings, sources=sources, graph=graph)

@app.get("/api/v1/investigations")
def list_investigations(user_id: str = Depends(current_user)):
    """Newest-first, owner-scoped dashboard history."""
    if not database_configured():
        items = [item for item in investigations.values() if item["user_id"] == user_id]
        return {"items": sorted(items, key=lambda item: item["created_at"], reverse=True)}
    result = get_supabase().table("investigations").select("id,company_name,job_title,risk_level,status,created_at,fee_detected").eq("user_id", user_id).order("created_at", desc=True).limit(50).execute()
    return {"items": result.data or []}

@app.delete("/api/v1/investigations/{investigation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_investigation(investigation_id: str, user_id: str = Depends(current_user)):
    """Delete only the caller's record; database cascades remove report and findings."""
    result = get_supabase().table("investigations").delete().eq("id", investigation_id).eq("user_id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Investigation not found.")

@app.post("/api/v1/investigations/{investigation_id}/rerun", response_model=InvestigationAccepted, status_code=status.HTTP_202_ACCEPTED)
async def rerun_investigation(investigation_id: str, user_id: str = Depends(current_user)):
    if not database_configured():
        source = [investigations[investigation_id]] if investigation_id in investigations and investigations[investigation_id]["user_id"] == user_id else []
    else:
        source = get_supabase().table("investigations").select("input_type,job_url,job_text,recruiter_name,recruiter_email,recruiter_phone").eq("id", investigation_id).eq("user_id", user_id).execute().data
    if not source:
        raise HTTPException(status_code=404, detail="Investigation not found.")
    row = source[0]
    payload = InvestigationCreate(input_type=row["input_type"], job_url=row.get("job_url"), job_text=row.get("job_text"))
    return await create_investigation(payload, user_id)
