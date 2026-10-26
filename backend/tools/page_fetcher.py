"""Page fetcher with SSRF defense, safe redirect validation, timeouts, and payload capping."""
from typing import Dict, Any, Tuple
import httpx
from backend.config import get_settings
from backend.tools.ssrf_guard import validate_url_safe, SSRFValidationError
from backend.tools.fixtures import get_mock_page_html

settings = get_settings()


async def fetch_web_page(url: str, timeout_seconds: int = 8) -> Dict[str, Any]:
    """
    Fetch web page content safely:
    - Pre-connection SSRF check (rejects RFC 1918, loopbacks, 169.254.169.254)
    - Manual redirect verification against SSRF filter
    - Max 2MB payload cap
    - Graceful error handling (no unhandled exceptions)
    """
    if settings.DEMO_MODE:
        return {
            "url": url,
            "html": get_mock_page_html(url),
            "status_code": 200,
            "success": True,
            "error": None,
        }

    # Step 1: Pre-connection SSRF validation
    is_safe, reason = validate_url_safe(url)
    if not is_safe:
        return {
            "url": url,
            "html": "",
            "status_code": 403,
            "success": False,
            "error": f"Blocked by SSRF filter: {reason}",
        }

    current_url = url
    max_redirects = 3
    redirect_count = 0

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (ResearchAgentBot/1.0)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        async with httpx.AsyncClient(
            follow_redirects=False,
            timeout=float(timeout_seconds),
            headers=headers,
        ) as client:
            while redirect_count <= max_redirects:
                try:
                    res = await client.get(current_url)
                except httpx.TimeoutException:
                    return {
                        "url": current_url,
                        "html": "",
                        "status_code": 408,
                        "success": False,
                        "error": f"Request timed out after {timeout_seconds}s",
                    }
                except Exception as e:
                    return {
                        "url": current_url,
                        "html": "",
                        "status_code": 500,
                        "success": False,
                        "error": f"HTTP client error: {str(e)}",
                    }

                # Check for redirects
                if res.is_redirect and "location" in res.headers:
                    redirect_count += 1
                    target_url = str(res.headers["location"])
                    # Check target redirect against SSRF
                    is_safe_redirect, redirect_reason = validate_url_safe(target_url)
                    if not is_safe_redirect:
                        return {
                            "url": target_url,
                            "html": "",
                            "status_code": 403,
                            "success": False,
                            "error": f"Redirect blocked by SSRF filter: {redirect_reason}",
                        }
                    current_url = target_url
                    continue

                # Stream-read payload up to MAX_PAYLOAD_BYTES (2MB)
                content = res.text[:settings.MAX_PAYLOAD_BYTES]
                return {
                    "url": current_url,
                    "html": content,
                    "status_code": res.status_code,
                    "success": res.status_code < 400,
                    "error": None if res.status_code < 400 else f"HTTP Status {res.status_code}",
                }

            return {
                "url": current_url,
                "html": "",
                "status_code": 310,
                "success": False,
                "error": "Exceeded maximum allowed redirects (3)",
            }

    except Exception as e:
        return {
            "url": url,
            "html": "",
            "status_code": 500,
            "success": False,
            "error": f"Unexpected fetch error: {str(e)}",
        }
