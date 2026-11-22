import io
import re
import asyncio
from typing import List, Optional, Tuple
import httpx
from bs4 import BeautifulSoup
import pypdf

from app.core.logging import logger
from app.schemas.claim import SearchResultItem
from app.schemas.document import ProcessedDocument
from app.utils.source_quality import source_quality_evaluator

# Boilerplate phrases commonly found in web scraping artifacts
BOILERPLATE_PATTERNS = [
    r"cookie\s*policy",
    r"all\s*rights\s*reserved",
    r"privacy\s*policy",
    r"terms\s*of\s*(service|use)",
    r"subscribe\s*to\s*our\s*newsletter",
    r"sign\s*up\s*for\s*free",
    r"accept\s*all\s*cookies",
    r"advertisement",
    r"share\s*this\s*article",
]

# Elements to strip from HTML
STRIP_TAGS = [
    "script", "style", "nav", "header", "footer", "aside", "noscript",
    "svg", "iframe", "form", "button", "dialog", "menu", "select",
    "textarea", "input", "figure", "figcaption",
]


class DocumentProcessor:
    """Fetches, extracts, sanitizes, and structures web and PDF documents."""

    def __init__(
        self,
        timeout_seconds: float = 4.0,
        max_bytes: int = 5 * 1024 * 1024,  # 5 MB max per document
        min_content_length: int = 60,
    ):
        self.timeout = timeout_seconds
        self.max_bytes = max_bytes
        self.min_content_length = min_content_length
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

    @staticmethod
    def clean_text(raw_text: str) -> str:
        """Sanitizes text, normalizes unicode spaces, and collapses extraneous whitespace while preserving paragraphs."""
        if not raw_text:
            return ""

        # Normalize unicode spaces and quotes
        text = raw_text.replace("\xa0", " ").replace("\r", "")
        text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")

        # Remove common boilerplate lines
        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                continue
            # Check boilerplate
            lower_line = trimmed.lower()
            if any(re.search(pat, lower_line) for pat in BOILERPLATE_PATTERNS) and len(trimmed) < 100:
                continue
            cleaned_lines.append(trimmed)

        joined = "\n\n".join(cleaned_lines)
        # Collapse multiple spaces
        joined = re.sub(r"[ \t]+", " ", joined)
        return joined.strip()

    @classmethod
    def extract_html(cls, html_bytes: bytes, fallback_url: str = "") -> Tuple[str, str, Optional[str], Optional[str]]:
        """Parses HTML, removes navigation/scripts, extracts main article content, and pulls metadata.
        
        Returns: (cleaned_content, title, author, publication_date)
        """
        try:
            soup = BeautifulSoup(html_bytes, "html.parser")
        except Exception as e:
            logger.warning("BeautifulSoup parsing failed: %s", str(e))
            return "", "Untitled", None, None

        # Extract metadata
        title = ""
        og_title = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "twitter:title"})
        if og_title and og_title.get("content"):
            title = og_title["content"].strip()
        elif soup.title and soup.title.string:
            title = soup.title.string.strip()
        if not title:
            title = source_quality_evaluator.extract_domain(fallback_url).capitalize() or "Web Document"

        # Author
        author = None
        author_meta = soup.find("meta", attrs={"name": "author"}) or soup.find("meta", property="article:author")
        if author_meta and author_meta.get("content"):
            author = author_meta["content"].strip()

        # Publication date
        pub_date = None
        date_meta = (
            soup.find("meta", property="article:published_time")
            or soup.find("meta", attrs={"name": "date"})
            or soup.find("meta", attrs={"name": "pubdate"})
        )
        if date_meta and date_meta.get("content"):
            pub_date = date_meta["content"].strip()[:10]
        else:
            time_tag = soup.find("time")
            if time_tag:
                pub_date = time_tag.get("datetime") or time_tag.get_text(strip=True)
                if pub_date:
                    pub_date = pub_date[:10]

        # Strip unneeded elements
        for tag in soup.find_all(STRIP_TAGS):
            tag.decompose()

        # Prioritize main article semantic containers if available
        article_elem = soup.find("article") or soup.find("main") or soup.find("div", class_=re.compile(r"article|content|post-body", re.I))
        target_container = article_elem if article_elem else soup.body or soup

        # Extract text from paragraphs or container
        paragraphs = target_container.find_all("p")
        if paragraphs and len(paragraphs) >= 2:
            raw_text = "\n\n".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20)
        else:
            raw_text = target_container.get_text(separator="\n", strip=True)

        cleaned = cls.clean_text(raw_text)
        return cleaned, title, author, pub_date

    @classmethod
    def extract_pdf(cls, pdf_bytes: bytes, max_pages: int = 15) -> Tuple[str, str, Optional[str], Optional[str]]:
        """Extracts text content and metadata from a PDF file."""
        try:
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            title = "PDF Document"
            author = None
            pub_date = None

            if reader.metadata:
                title = reader.metadata.title or "PDF Document"
                author = reader.metadata.author

            text_parts = []
            pages_to_read = min(len(reader.pages), max_pages)
            for i in range(pages_to_read):
                page_text = reader.pages[i].extract_text()
                if page_text:
                    text_parts.append(page_text)

            raw_text = "\n\n".join(text_parts)
            cleaned = cls.clean_text(raw_text)
            return cleaned, title, author, pub_date
        except Exception as e:
            logger.warning("PDF extraction failed: %s", str(e))
            return "", "PDF Document", None, None

    async def fetch_document(self, candidate: SearchResultItem) -> ProcessedDocument:
        """Fetches and extracts a single candidate web document with timeouts, size limits, and fallback."""
        url = candidate.url
        domain = candidate.domain or source_quality_evaluator.extract_domain(url)
        quality = candidate.quality_assessment or source_quality_evaluator.evaluate(url)

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf,*/*;q=0.8",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    raise httpx.HTTPStatusError(
                        f"HTTP {resp.status_code}", request=resp.request, response=resp
                    )

                content_bytes = resp.content
                if len(content_bytes) > self.max_bytes:
                    content_bytes = content_bytes[: self.max_bytes]

                content_type_header = resp.headers.get("content-type", "").lower()

                if "application/pdf" in content_type_header or url.lower().endswith(".pdf"):
                    content, title, author, pub_date = self.extract_pdf(content_bytes)
                    doc_type = "pdf"
                else:
                    content, title, author, pub_date = self.extract_html(content_bytes, fallback_url=url)
                    doc_type = "html"

                # Prefer candidate snippet's title or publication date if extraction did not discover them
                final_title = title if title and title != "Web Document" else candidate.title or "Web Document"
                final_pub_date = pub_date or candidate.publication_date

                is_usable = len(content) >= self.min_content_length

                # If extracted content was too thin, fall back to snippet
                if not is_usable and candidate.snippet and len(candidate.snippet) >= 30:
                    content = f"{final_title}\n\n{candidate.snippet}"
                    is_usable = True
                    doc_type = "snippet_fallback"

                return ProcessedDocument(
                    url=url,
                    title=final_title,
                    domain=domain,
                    content=content,
                    cleaned_length=len(content),
                    content_type=doc_type,
                    author=author,
                    publication_date=final_pub_date,
                    source_quality=quality,
                    is_usable=is_usable,
                    extraction_error=None,
                )

        except Exception as e:
            logger.info("Live document fetch failed for '%s' (%s); using search snippet fallback.", url, str(e))
            # Fallback to search snippet
            fallback_content = f"{candidate.title}\n\n{candidate.snippet}" if candidate.snippet else ""
            return ProcessedDocument(
                url=url,
                title=candidate.title or "Web Document",
                domain=domain,
                content=fallback_content,
                cleaned_length=len(fallback_content),
                content_type="snippet_fallback",
                publication_date=candidate.publication_date,
                source_quality=quality,
                is_usable=len(fallback_content) >= 30,
                extraction_error=str(e),
            )

    async def process_candidates(
        self,
        candidates: List[SearchResultItem],
        max_concurrent: int = 5,
    ) -> List[ProcessedDocument]:
        """Fetches and processes candidate documents concurrently."""
        if not candidates:
            return []

        semaphore = asyncio.Semaphore(max_concurrent)

        async def _bounded_fetch(item: SearchResultItem) -> ProcessedDocument:
            async with semaphore:
                return await self.fetch_document(item)

        tasks = [_bounded_fetch(item) for item in candidates]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_docs: List[ProcessedDocument] = []
        for res in results:
            if isinstance(res, ProcessedDocument):
                processed_docs.append(res)
            elif isinstance(res, Exception):
                logger.warning("Document processing encountered unexpected exception: %s", str(res))

        # Filter and prioritize usable documents
        usable_docs = [d for d in processed_docs if d.is_usable]
        logger.info(
            "Processed %d candidates: %d usable, %d rejected/empty.",
            len(candidates),
            len(usable_docs),
            len(processed_docs) - len(usable_docs),
        )
        return usable_docs if usable_docs else processed_docs


document_processor = DocumentProcessor()
