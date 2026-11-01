import re
from urllib.parse import urlparse

import httpx

from app.core.config import get_settings
from app.models.schemas import Finding, Source


EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
COMPANY_RE = re.compile(r"(?:company|employer|organization|hiring\s+company)\s*[:\-]\s*([^\n|]{2,100})", re.I)
ROLE_RE = re.compile(r"(?:job\s+title|role|position)\s*[:\-]\s*([^\n|]{2,100})", re.I)
PUBLIC_EMAIL_DOMAINS = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "proton.me"}


def _clean(value: str | None) -> str | None:
    if not value:
        return None
    return re.sub(r"\s+", " ", value).strip(" .,:;|-\t")[:120] or None


def extract_entities(text: str, source_url: str | None = None) -> dict[str, str | None]:
    email = EMAIL_RE.search(text)
    company = COMPANY_RE.search(text)
    role = ROLE_RE.search(text)
    domain = urlparse(source_url).hostname if source_url else None
    if not company and domain and domain not in {"linkedin.com", "indeed.com", "naukri.com"}:
        company_name = domain.removeprefix("www.").split(".")[0].replace("-", " ").title()
    else:
        company_name = _clean(company.group(1) if company else None)
    return {"company_name": company_name, "job_title": _clean(role.group(1) if role else None), "recruiter_email": email.group(0).lower() if email else None}


async def verify_listing(text: str, source_url: str | None = None) -> tuple[dict[str, str | None], list[Finding], list[Source]]:
    entities = extract_entities(text, source_url)
    findings: list[Finding] = []
    sources: list[Source] = []
    company = entities.get("company_name")
    email = entities.get("recruiter_email")
    if email:
        email_domain = email.rsplit("@", 1)[1]
        if email_domain in PUBLIC_EMAIL_DOMAINS:
            findings.append(Finding(title="Recruiter uses a public email domain", detail="The listing uses a mailbox provider rather than an identifiable company domain.", status="warning", quote=email))
        elif company and not any(token in email_domain for token in re.findall(r"[a-z0-9]+", company.lower()) if len(token) > 2):
            findings.append(Finding(title="Recruiter domain differs from company name", detail="The recruiter email domain does not visibly match the named company. Verify through an official company contact.", status="unverified", quote=email))
        else:
            findings.append(Finding(title="Recruiter email domain is consistent", detail="The recruiter email domain contains a token matching the named company.", status="verified", quote=email))

    settings = get_settings()
    if company and settings.tinyfish_api_key and not settings.tinyfish_api_key.startswith("replace-"):
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(
                    "https://api.search.tinyfish.ai",
                    params={"query": f"{company} official careers"},
                    headers={"X-API-Key": settings.tinyfish_api_key},
                )
                response.raise_for_status()
                results = response.json().get("results", [])
                first = results[0] if results else {}
                result_url = first.get("url") or first.get("link")
                if result_url:
                    sources.append(Source(url=result_url, title=f"{company} careers search result", source_type="web_search"))
                    findings.append(Finding(title="Official careers page candidate found", detail="A public search result may provide an official company careers page. Open the source and verify the role independently.", status="unverified", quote=result_url))
        except (httpx.HTTPError, IndexError, KeyError, TypeError, ValueError):
            pass
    return entities, findings, sources
