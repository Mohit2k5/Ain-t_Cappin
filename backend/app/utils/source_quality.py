import re
from urllib.parse import urlparse
from typing import Dict, List, Optional
from app.schemas.claim import SourceQualityAssessment

# Known authoritative domain registries
GOVERNMENT_DOMAINS = {
    "gov", "mil", "int", "europa.eu", "who.int", "un.org", "cdc.gov",
    "nih.gov", "nasa.gov", "noaa.gov", "fda.gov", "usgs.gov", "esa.int",
    "cern.ch", "gov.uk", "canada.ca", "australia.gov.au",
}

ACADEMIC_SCIENTIFIC_DOMAINS = {
    "edu", "ac.uk", "nature.com", "science.org", "thelancet.com",
    "sciencedirect.com", "nejm.org", "jamanetwork.com", "arxiv.org",
    "ncbi.nlm.nih.gov", "pnas.org", "cell.com", "bmj.com", "ieee.org",
    "springer.com", "wiley.com", "oup.com", "cambridge.org",
}

FACT_CHECKING_DOMAINS = {
    "snopes.com", "politifact.com", "factcheck.org", "fullfact.org",
    "leadstories.com", "climatefeedback.org", "healthfeedback.org",
    "checkyourfact.com", "afp.com", "reuters.com", "apnews.com",
}

ESTABLISHED_NEWS_DOMAINS = {
    "reuters.com", "apnews.com", "bbc.com", "bbc.co.uk", "npr.org",
    "pbs.org", "theguardian.com", "nytimes.com", "washingtonpost.com",
    "wsj.com", "ft.com", "economist.com", "bloomberg.com", "dw.com",
    "aljazeera.com", "time.com", "scientificamerican.com", "nationalgeographic.com",
}

USER_GENERATED_SOCIAL_DOMAINS = {
    "reddit.com", "twitter.com", "x.com", "facebook.com", "tiktok.com",
    "instagram.com", "quora.com", "medium.com", "substack.com",
    "youtube.com", "threads.net", "pinterest.com", "tumblr.com",
}

SATIRE_OR_UNRELIABLE_DOMAINS = {
    "theonion.com", "babylonbee.com", "newshump.com", "dailycurrant.com",
    "infowars.com", "naturalnews.com", "beforeitsnews.com",
}


class SourceQualityEvaluator:
    """Evaluates source credibility, organizational affiliation, and contextual reliability.
    
    Adheres strictly to the principle: Domain reputation alone is not proof of factual correctness.
    """

    @staticmethod
    def extract_domain(url: str) -> str:
        """Extracts normalized base domain from a URL."""
        if not url:
            return ""
        parsed = urlparse(url if "://" in url else f"https://{url}")
        netloc = parsed.netloc.lower()
        # Strip port
        if ":" in netloc:
            netloc = netloc.split(":")[0]
        # Strip leading www.
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc

    @classmethod
    def evaluate(
        cls,
        url: str,
        title: Optional[str] = None,
        snippet: Optional[str] = None,
        publication_date: Optional[str] = None,
    ) -> SourceQualityAssessment:
        domain = cls.extract_domain(url)
        notes: List[str] = []
        is_primary = False
        quality_score = 50.0
        affiliation = "Unknown"
        credibility_tier = "Moderate"

        if not domain:
            return SourceQualityAssessment(
                domain="unknown",
                credibility_tier="Low",
                affiliation="Unknown",
                quality_score=20.0,
                is_primary_source_likely=False,
                notes=["Empty or unparseable URL provided."],
            )

        tld = domain.split(".")[-1]
        domain_parts = domain.split(".")
        second_level_tld = ".".join(domain_parts[-2:]) if len(domain_parts) >= 2 else ""

        # Check Satire / Unreliable
        if any(satire in domain for satire in SATIRE_OR_UNRELIABLE_DOMAINS):
            affiliation = "Satire / Known Unreliable"
            credibility_tier = "Low"
            quality_score = 15.0
            notes.append("Domain is categorized as satire, parody, or consistently unreliable.")
            is_primary = False

        # Check Government / Multilateral
        elif (
            tld in {"gov", "mil", "int"}
            or second_level_tld in {"gov.uk", "canada.ca", "australia.gov.au"}
            or any(gov in domain for gov in GOVERNMENT_DOMAINS)
        ):
            affiliation = "Government"
            credibility_tier = "High"
            quality_score = 92.0
            is_primary = True
            notes.append("Official government or intergovernmental public domain.")
            notes.append("Subject to regulatory and official record standards.")

        # Check Academic / Scientific
        elif (
            tld in {"edu"}
            or second_level_tld in {"ac.uk", "edu.au", "ac.in"}
            or any(acad in domain for acad in ACADEMIC_SCIENTIFIC_DOMAINS)
        ):
            affiliation = "Academic/Scientific"
            credibility_tier = "High"
            quality_score = 90.0
            is_primary = True
            notes.append("Peer-reviewed journal, university repository, or scientific publisher.")
            notes.append("Strong institutional citations and methodology oversight.")

        # Check Verified Fact-Checking Organization
        elif any(fc in domain for fc in FACT_CHECKING_DOMAINS):
            affiliation = "Fact-Checking"
            credibility_tier = "High"
            quality_score = 88.0
            is_primary = False
            notes.append("Dedicated fact-checking or wire service verification bureau.")
            notes.append("Employs explicit evidence cross-examination protocols.")

        # Check Major News & Journalism
        elif any(news in domain for news in ESTABLISHED_NEWS_DOMAINS):
            affiliation = "Major News/Journalism"
            credibility_tier = "Moderate"
            quality_score = 78.0
            is_primary = False
            notes.append("Established journalistic organization with editorial review standards.")

        # Check User-Generated / Social Media
        elif any(social in domain for social in USER_GENERATED_SOCIAL_DOMAINS):
            affiliation = "Social / User-Generated"
            credibility_tier = "Caution"
            quality_score = 35.0
            is_primary = False
            notes.append("User-generated platform: claims require independent primary corroboration.")

        # Generic commercial or blog domain
        else:
            affiliation = "Commercial/Independent"
            credibility_tier = "Moderate"
            quality_score = 52.0
            is_primary = False
            notes.append("Independent web source: verify claims against authoritative primary sources.")

        # Adjust score based on publication date availability
        if publication_date:
            quality_score = min(100.0, quality_score + 3.0)
            notes.append(f"Publication date documented: {publication_date}.")
        else:
            notes.append("No explicit publication date detected in metadata.")

        # Add vital principle reminder
        notes.append("Domain reputation serves as an indicator of editorial process, not an absolute guarantee of factual correctness.")

        return SourceQualityAssessment(
            domain=domain,
            credibility_tier=credibility_tier,
            affiliation=affiliation,
            quality_score=round(quality_score, 1),
            is_primary_source_likely=is_primary,
            notes=notes,
        )


source_quality_evaluator = SourceQualityEvaluator()
