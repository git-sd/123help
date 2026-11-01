import ipaddress
import socket
from html.parser import HTMLParser
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException
from app.core.config import get_settings


MAX_BYTES = 250_000


class _VisibleTextParser(HTMLParser):
    ignored = {"script", "style", "noscript", "svg"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() in self.ignored:
            self.depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self.ignored and self.depth:
            self.depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.depth and data.strip():
            self.parts.append(data.strip())


def visible_text(markup: str) -> str:
    parser = _VisibleTextParser()
    parser.feed(markup)
    return " ".join(parser.parts)


def _assert_safe_host(hostname: str) -> None:
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)}
    except socket.gaierror as exc:
        raise HTTPException(422, "The listing host could not be resolved.") from exc
    for address in addresses:
        parsed = ipaddress.ip_address(address)
        if not parsed.is_global:
            raise HTTPException(422, "Private and local URLs are not allowed.")


async def fetch_listing(url: str) -> tuple[str, str]:
    """Fetch a small public HTML page without following redirects or private hosts."""
    parsed = urlparse(url)
    if not parsed.hostname:
        raise HTTPException(422, "Enter a valid public http(s) URL.")
    _assert_safe_host(parsed.hostname)
    settings = get_settings()
    if settings.tinyfish_api_key and not settings.tinyfish_api_key.startswith("replace-"):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    settings.tinyfish_fetch_url,
                    headers={"X-API-Key": settings.tinyfish_api_key, "Content-Type": "application/json"},
                    json={"urls": [url], "format": "markdown", "links": True},
                )
                response.raise_for_status()
                result = response.json().get("results", [])[0]
                text = result.get("text") or result.get("content") or ""
                if text.strip():
                    return text[:MAX_BYTES], result.get("url", url)
        except (httpx.HTTPError, IndexError, KeyError, TypeError, ValueError):
            # Fall through to the bounded direct fetcher.
            pass
    headers = {"User-Agent": "GhostJob/0.1 (+public listing verification)"}
    try:
        async with httpx.AsyncClient(follow_redirects=False, timeout=10.0, headers=headers) as client:
            response = await client.get(url)
            if response.status_code in {301, 302, 303, 307, 308}:
                raise HTTPException(422, "Redirected listings are not supported yet. Paste the job description instead.")
            response.raise_for_status()
            content = response.content[:MAX_BYTES]
    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        raise HTTPException(422, "We could not read that public listing. Paste the job description instead.") from exc
    text = content.decode(response.encoding or "utf-8", errors="ignore")
    return visible_text(text), str(response.url)
