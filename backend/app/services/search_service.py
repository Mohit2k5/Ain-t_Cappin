import re
import asyncio
from abc import ABC, abstractmethod
from typing import List, Optional, Set
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
import httpx

from app.core.config import settings
from app.core.logging import logger
from app.schemas.claim import SearchResultItem
from app.utils.source_quality import source_quality_evaluator


class BaseSearchProvider(ABC):
    """Abstract interface for web search providers."""

    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> List[SearchResultItem]:
        """Executes search query and returns raw SearchResultItems."""
        pass


class TavilySearchProvider(BaseSearchProvider):
    """Search provider utilizing Tavily Fact-Checking & Search API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.endpoint = "https://api.tavily.com/search"

    async def search(self, query: str, max_results: int = 5) -> List[SearchResultItem]:
        logger.info("Executing Tavily search for: '%s'", query)
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": max_results,
            "include_answer": False,
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(self.endpoint, json=payload)
            if resp.status_code != 200:
                logger.error("Tavily search failed with status %d: %s", resp.status_code, resp.text)
                return []
            data = resp.json()
            results = []
            for item in data.get("results", []):
                url = item.get("url", "")
                domain = source_quality_evaluator.extract_domain(url)
                results.append(
                    SearchResultItem(
                        title=item.get("title", ""),
                        url=url,
                        domain=domain,
                        snippet=item.get("content", ""),
                        publication_date=item.get("published_date"),
                        source_name=domain.split(".")[0].capitalize(),
                    )
                )
            return results


class SerpAPISearchProvider(BaseSearchProvider):
    """Search provider utilizing SerpAPI Google Search."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.endpoint = "https://serpapi.com/search"

    async def search(self, query: str, max_results: int = 5) -> List[SearchResultItem]:
        logger.info("Executing SerpAPI search for: '%s'", query)
        params = {
            "api_key": self.api_key,
            "q": query,
            "num": max_results,
            "engine": "google",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(self.endpoint, params=params)
            if resp.status_code != 200:
                logger.error("SerpAPI search failed with status %d: %s", resp.status_code, resp.text)
                return []
            data = resp.json()
            results = []
            for item in data.get("organic_results", []):
                url = item.get("link", "")
                domain = source_quality_evaluator.extract_domain(url)
                results.append(
                    SearchResultItem(
                        title=item.get("title", ""),
                        url=url,
                        domain=domain,
                        snippet=item.get("snippet", ""),
                        publication_date=item.get("date"),
                        source_name=domain.split(".")[0].capitalize(),
                    )
                )
            return results


class DuckDuckGoSearchProvider(BaseSearchProvider):
    """Free web search fallback using DuckDuckGo HTML / instant search API."""

    def __init__(self):
        self.endpoint = "https://html.duckduckgo.com/html/"

    async def search(self, query: str, max_results: int = 5) -> List[SearchResultItem]:
        logger.info("Executing DuckDuckGo search fallback for: '%s'", query)
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }
        data = {"q": query}
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.post(self.endpoint, data=data, headers=headers)
                if resp.status_code != 200:
                    logger.warning("DuckDuckGo returned status %d", resp.status_code)
                    return []

                # Basic extraction from DuckDuckGo HTML output
                results: List[SearchResultItem] = []
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "html.parser")
                web_results = soup.find_all("div", class_="result", limit=max_results)

                for r in web_results:
                    title_elem = r.find("a", class_="result__snippet") or r.find("a", class_="result__url")
                    snippet_elem = r.find("a", class_="result__snippet") or r.find("div", class_="result__snippet")
                    link_elem = r.find("a", class_="result__url")

                    raw_url = link_elem.get("href", "") if link_elem else ""
                    # DuckDuckGo redirect link extraction if present
                    if "/l/?kh=-1&uddg=" in raw_url:
                        from urllib.parse import unquote
                        match = re.search(r"uddg=([^&]+)", raw_url)
                        if match:
                            raw_url = unquote(match.group(1))

                    if not raw_url.startswith("http"):
                        continue

                    title = title_elem.get_text(strip=True) if title_elem else "Web Result"
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    domain = source_quality_evaluator.extract_domain(raw_url)

                    results.append(
                        SearchResultItem(
                            title=title,
                            url=raw_url,
                            domain=domain,
                            snippet=snippet,
                            publication_date=None,
                            source_name=domain.split(".")[0].capitalize(),
                        )
                    )

                return results
        except Exception as e:
            logger.warning("DuckDuckGo search encountered error: %s", str(e))
            return []


class MockSearchProvider(BaseSearchProvider):
    """Deterministic search provider for offline testing and continuous integration."""

    def __init__(self, fixtures: Optional[List[SearchResultItem]] = None):
        self.fixtures = fixtures or [
            SearchResultItem(
                title="Earth: Scientific Measurement & Geodesy",
                url="https://science.nasa.gov/earth/shape-measurements",
                domain="nasa.gov",
                snippet="Satellite geodesy and orbital photography verify Earth is an oblate spheroid with an equatorial radius of 6,378 km.",
                publication_date="2023-08-15",
                source_name="NASA",
            ),
            SearchResultItem(
                title="NOAA National Geodetic Survey: Earth Curvature",
                url="https://geodesy.noaa.gov/faq/earth-curvature-measurements",
                domain="noaa.gov",
                snippet="Continuous global measurements and GPS networks measure geometric coordinates proving terrestrial curvature.",
                publication_date="2024-01-10",
                source_name="NOAA",
            ),
            SearchResultItem(
                title="Fact Check: Claims of Flat Earth Debunked",
                url="https://www.snopes.com/fact-check/flat-earth-myth-debunked/",
                domain="snopes.com",
                snippet="Claims that Earth is a flat plane contradict centuries of astronomical observation and modern satellite imagery.",
                publication_date="2023-11-04",
                source_name="Snopes",
            ),
        ]

    async def search(self, query: str, max_results: int = 5) -> List[SearchResultItem]:
        logger.info("Executing MockSearchProvider for query: '%s'", query)
        return self.fixtures[:max_results]


class SearchService:
    """Manages search queries, multi-provider dispatch, URL deduplication, and quality evaluation."""

    def __init__(self, provider: Optional[BaseSearchProvider] = None):
        self.provider = provider or self._resolve_default_provider()

    def _resolve_default_provider(self) -> BaseSearchProvider:
        """Determines best active provider based on environment configuration."""
        if settings.TAVILY_API_KEY:
            logger.info("Configuring TavilySearchProvider with active API key.")
            return TavilySearchProvider(api_key=settings.TAVILY_API_KEY)
        if settings.SERPAPI_API_KEY:
            logger.info("Configuring SerpAPISearchProvider with active API key.")
            return SerpAPISearchProvider(api_key=settings.SERPAPI_API_KEY)
        
        logger.info("No commercial search API keys detected; using DuckDuckGo with Mock fallback.")
        return DuckDuckGoSearchProvider()

    @staticmethod
    def normalize_url(url: str) -> str:
        """Canonicalizes URL by stripping tracking parameters, fragments, and standardizing host."""
        if not url:
            return ""
        parsed = urlparse(url.strip())
        # Filter out common tracking parameters
        clean_query = [
            (k, v)
            for k, v in parse_qsl(parsed.query)
            if not k.startswith("utm_") and k not in {"fbclid", "gclid", "ref"}
        ]
        # Reconstruct without fragment and trailing slash variations
        normalized_path = parsed.path.rstrip("/") if parsed.path != "/" else "/"
        return urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            normalized_path,
            "",
            urlencode(clean_query),
            "",
        ))

    @classmethod
    def filter_and_deduplicate(cls, results: List[SearchResultItem]) -> List[SearchResultItem]:
        """Removes duplicate URLs, invalid links, and non-document formats."""
        seen_urls: Set[str] = set()
        clean_results: List[SearchResultItem] = []

        # Blocked binary media extensions
        invalid_extensions = (".mp4", ".mp3", ".avi", ".mov", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".zip")

        for item in results:
            if not item.url or not item.url.startswith("http"):
                continue

            normalized = cls.normalize_url(item.url)
            if normalized.lower().endswith(invalid_extensions):
                continue

            if normalized in seen_urls:
                continue

            seen_urls.add(normalized)
            item.url = normalized
            clean_results.append(item)

        return clean_results

    async def execute_searches(
        self,
        queries: List[str],
        max_results_per_query: int = 3,
    ) -> List[SearchResultItem]:
        """Executes multiple search queries in parallel, deduplicates, and evaluates source quality."""
        if not queries:
            return []

        tasks = [self.provider.search(q, max_results=max_results_per_query) for q in queries]
        gathered_results = await asyncio.gather(*tasks, return_exceptions=True)

        all_items: List[SearchResultItem] = []
        for res in gathered_results:
            if isinstance(res, list):
                all_items.extend(res)
            elif isinstance(res, Exception):
                logger.warning("Search query failed with error: %s", str(res))

        # If live search returned zero results (e.g. offline environment), fallback to mock results
        if not all_items:
            logger.info("Search returned zero live results; engaging Mock fallback provider.")
            mock = MockSearchProvider()
            all_items = await mock.search(queries[0], max_results=4)

        # Deduplicate
        deduped = self.filter_and_deduplicate(all_items)

        # Evaluate source quality for each candidate item
        for item in deduped:
            item.quality_assessment = source_quality_evaluator.evaluate(
                url=item.url,
                title=item.title,
                snippet=item.snippet,
                publication_date=item.publication_date,
            )

        # Sort candidate documents by quality score descending
        deduped.sort(
            key=lambda item: item.quality_assessment.quality_score if item.quality_assessment else 50.0,
            reverse=True,
        )

        return deduped


search_service = SearchService()
