"""Web search tool supporting Tavily, DuckDuckGo, and deterministic offline mock."""
from typing import Any, Dict, List
import httpx
from backend.config import get_settings
from backend.tools.fixtures import get_mock_search_results

settings = get_settings()


class WebSearchError(Exception):
    """Raised when web search fails."""
    pass


async def search_tavily(query: str, api_key: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Execute search query using Tavily API."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
                "include_answer": False,
            },
        )
        response.raise_for_status()
        data = response.json()
        results = []
        for item in data.get("results", []):
            results.append({
                "url": item.get("url", ""),
                "title": item.get("title", ""),
                "snippet": item.get("content", ""),
            })
        return results


async def search_duckduckgo(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Execute search query using DuckDuckGo HTML/Instant Answer."""
    try:
        url = "https://html.duckduckgo.com/html/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
            res = await client.post(url, data={"q": query}, follow_redirects=True)
            res.raise_for_status()
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(res.text, "html.parser")
            results = []
            for r in soup.select(".result")[:max_results]:
                title_elem = r.select_one(".result__title a")
                snippet_elem = r.select_one(".result__snippet")
                if title_elem and title_elem.get("href"):
                    results.append({
                        "url": title_elem["href"],
                        "title": title_elem.get_text(strip=True),
                        "snippet": snippet_elem.get_text(strip=True) if snippet_elem else "",
                    })
            if results:
                return results
    except Exception:
        pass
    # Fallback if DuckDuckGo blocks or fails
    return get_mock_search_results(query, max_results)


async def execute_web_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Primary search tool entrypoint.
    Chooses between Tavily, DuckDuckGo, and Mock based on configuration and DEMO_MODE.
    """
    clean_query = query.strip()
    if not clean_query:
        return []

    # Demo mode or explicit mock provider
    if settings.DEMO_MODE or settings.SEARCH_PROVIDER == "mock":
        return get_mock_search_results(clean_query, max_results)

    # Tavily
    if settings.SEARCH_PROVIDER == "tavily" and settings.TAVILY_API_KEY:
        try:
            return await search_tavily(clean_query, settings.TAVILY_API_KEY, max_results)
        except Exception:
            # Fallback to mock search on external API failure
            return get_mock_search_results(clean_query, max_results)

    # DuckDuckGo fallback
    if settings.SEARCH_PROVIDER == "duckduckgo":
        return await search_duckduckgo(clean_query, max_results)

    return get_mock_search_results(clean_query, max_results)
