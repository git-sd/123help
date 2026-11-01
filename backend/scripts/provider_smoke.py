"""Live provider smoke test. Run from backend/: python scripts/provider_smoke.py"""

import asyncio
import time

import httpx

from app.core.config import get_settings


async def check_gemini(settings) -> tuple[str, str]:
    if not settings.gemini_api_key or settings.gemini_api_key.startswith("replace-"):
        return "SKIP", "GEMINI_API_KEY is not configured"
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(endpoint, params={"key": settings.gemini_api_key}, json={
                "contents": [{"parts": [{"text": 'Return exactly the JSON object {"ok":true}.'}]}],
                "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
            })
            response.raise_for_status()
        return "PASS", f"model={settings.gemini_model}"
    except httpx.HTTPError as exc:
        return "FAIL", f"{type(exc).__name__}"


async def check_tinyfish(settings) -> tuple[str, str]:
    if not settings.tinyfish_api_key or settings.tinyfish_api_key.startswith("replace-"):
        return "SKIP", "TINYFISH_API_KEY is not configured"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get("https://api.search.tinyfish.ai", params={"query": "GhostJob"}, headers={"X-API-Key": settings.tinyfish_api_key})
            response.raise_for_status()
        return "PASS", "search endpoint reachable"
    except httpx.HTTPError as exc:
        return "FAIL", f"{type(exc).__name__}"


async def main() -> int:
    settings = get_settings()
    started = time.perf_counter()
    gemini, tinyfish = await asyncio.gather(check_gemini(settings), check_tinyfish(settings))
    print(f"Gemini:   {gemini[0]} — {gemini[1]}")
    print(f"TinyFish: {tinyfish[0]} — {tinyfish[1]}")
    print(f"Elapsed:  {time.perf_counter() - started:.2f}s")
    return 1 if "FAIL" in {gemini[0], tinyfish[0]} else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
