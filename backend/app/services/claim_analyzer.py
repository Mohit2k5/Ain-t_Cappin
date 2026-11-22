import re
from typing import List, Tuple
from app.core.logging import logger
from app.schemas.claim import ClaimCategory, ClaimAnalysisResult

# Lexical category keyword mappings
CATEGORY_KEYWORDS = {
    ClaimCategory.HEALTH: {
        "cancer", "cure", "vaccine", "vaccines", "vaccination", "autism", "virus", "covid",
        "disease", "hospital", "medicine", "medical", "doctor", "health", "diet", "lemon",
        "baking soda", "vitamin", "drugs", "pharmaceutical", "fda", "who", "cdc", "infection",
        "treatment", "symptoms", "therapy", "blood", "heart", "brain", "clinical",
    },
    ClaimCategory.SCIENCE: {
        "earth", "flat", "sphere", "globe", "space", "nasa", "planet", "orbit", "moon", "mars",
        "sun", "gravity", "physics", "climate", "global warming", "temperature", "biology",
        "chemistry", "quantum", "galaxy", "telescope", "species", "evolution", "dna",
        "atmosphere", "geology", "ocean", "energy", "noaa", "cern", "scientific",
    },
    ClaimCategory.POLITICS: {
        "president", "election", "vote", "voter", "ballot", "congress", "senate", "senator",
        "democrat", "republican", "parliament", "prime minister", "white house", "government",
        "law", "bill", "legislation", "supreme court", "constitution", "governor", "mayor",
        "treaty", "sanctions", "minister", "political", "campaign",
    },
    ClaimCategory.FINANCE: {
        "stock", "market", "inflation", "economy", "economic", "gdp", "interest rate", "dollar",
        "federal reserve", "fed", "bank", "banking", "crypto", "cryptocurrency", "bitcoin",
        "ethereum", "currency", "debt", "recession", "revenue", "profit", "nasdaq", "dow jones",
    },
    ClaimCategory.TECHNOLOGY: {
        "ai", "artificial intelligence", "robot", "robotics", "software", "computer", "internet",
        "algorithm", "apple", "google", "microsoft", "meta", "openai", "nvidia", "hardware",
        "smartphone", "chip", "semiconductor", "cybersecurity", "quantum computing", "5g",
    },
    ClaimCategory.HISTORY: {
        "war", "wwi", "wwii", "world war", "ancient", "century", "empire", "revolution",
        "pyramids", "rome", "roman", "medieval", "columbus", "lincoln", "hitler", "churchill",
        "declaration", "independence", "treaty of", "assassinated", "civil war", "dynasty",
    },
    ClaimCategory.CURRENT_EVENTS: {
        "breaking", "today", "yesterday", "this week", "announced", "recent", "recently",
        "summit", "signed", "crisis", "disaster", "earthquake", "flooding", "shooting",
        "hostage", "protest", "strike", "latest",
    },
}

COMMON_LOCATIONS = {
    "mars", "moon", "earth", "china", "united states", "usa", "us", "uk", "britain",
    "russia", "ukraine", "india", "japan", "germany", "france", "canada", "australia",
    "brazil", "africa", "asia", "europe", "antarctica", "washington", "beijing", "moscow",
    "london", "paris", "tokyo", "great wall of china",
}


class ClaimAnalyzer:
    """Analyzes claims, extracts entities, categorizes topics, and crafts multi-angle search queries.
    
    Adheres strictly to the requirement: The Claim Analyzer must not generate the final verdict.
    """

    @staticmethod
    def normalize_input(claim: str) -> str:
        """Cleans social media artifacts, hashtags, excess punctuation, and whitespace."""
        if not claim:
            return ""
        # Remove leading hashtags or handle mentions
        cleaned = re.sub(r"#([a-zA-Z0-9_]+)", r"\1", claim)
        cleaned = re.sub(r"@([a-zA-Z0-9_]+)", r"\1", cleaned)
        # Normalize whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        # Remove surrounding quotes if paired
        if (cleaned.startswith('"') and cleaned.endswith('"')) or (
            cleaned.startswith("'") and cleaned.endswith("'")
        ):
            cleaned = cleaned[1:-1].strip()
        return cleaned

    @staticmethod
    def extract_dates(text: str) -> List[str]:
        """Extracts years, decades, or date expressions."""
        dates = []
        # Match 4-digit years (e.g. 1969, 2024)
        year_matches = re.findall(r"\b(1[789]\d\d|20[0-2]\d)\b", text)
        dates.extend(year_matches)
        # Match common temporal phrases
        temporal_matches = re.findall(
            r"\b(yesterday|today|last week|recently|in the 19\d0s|in the 20\d0s)\b",
            text,
            re.IGNORECASE,
        )
        dates.extend(temporal_matches)
        return list(dict.fromkeys(dates))

    @staticmethod
    def extract_locations(text: str) -> List[str]:
        """Identifies geographical and astronomical locations."""
        lower_text = text.lower()
        found = []
        for loc in COMMON_LOCATIONS:
            pattern = rf"\b{re.escape(loc)}\b"
            if re.search(pattern, lower_text):
                found.append(loc.title())
        return found

    @staticmethod
    def extract_entities(text: str) -> List[str]:
        """Extracts prominent named entities and proper nouns."""
        entities = []
        # Extract sequences of capitalized words
        cap_matches = re.findall(r"\b[A-Z][a-zA-Z0-9]*(?:\s+[A-Z][a-zA-Z0-9]*)*\b", text)
        for m in cap_matches:
            if m.lower() not in {"the", "a", "an", "is", "are", "was", "were", "this", "that"}:
                entities.append(m)

        # Extract known acronyms
        acronyms = re.findall(r"\b[A-Z]{2,}\b", text)
        entities.extend(acronyms)

        # Remove duplicates preserving order
        unique_entities = []
        for e in entities:
            if e not in unique_entities and len(e) > 1:
                unique_entities.append(e)
        return unique_entities

    @classmethod
    def classify_category(cls, text: str) -> ClaimCategory:
        """Classifies the claim into one of the 8 canonical categories."""
        tokens = set(re.findall(r"\b[a-zA-Z]+\b", text.lower()))
        best_cat = ClaimCategory.GENERAL_FACTUAL
        highest_score = 0

        for category, keywords in CATEGORY_KEYWORDS.items():
            matches = len(tokens.intersection(keywords))
            if matches > highest_score:
                highest_score = matches
                best_cat = category

        return best_cat

    @classmethod
    def determine_verification_topic(cls, claim: str, category: ClaimCategory, entities: List[str]) -> str:
        """Determines the core question or assertion being verified."""
        if entities:
            primary_entity = entities[0]
            if "flat" in claim.lower() and "earth" in claim.lower():
                return "Earth's shape and curvature"
            if "water" in claim.lower() and "mars" in claim.lower():
                return "Existence of liquid water on Mars"
            if "cure" in claim.lower():
                return f"Medical efficacy of claimed cure involving {primary_entity}"
            return f"Factual accuracy of claims regarding {primary_entity}"
        return f"{category.value} assertion verification"

    @classmethod
    def generate_search_queries(
        cls,
        normalized_claim: str,
        category: ClaimCategory,
        entities: List[str],
        topic: str,
    ) -> List[str]:
        """Generates multi-perspective search queries for evidence retrieval:
        1. Neutral verification query
        2. Empirical evidence query with authoritative terminology
        3. Debunk / refutation angle query
        4. Primary institutional / consensus query
        """
        queries: List[str] = []

        # 1. Direct clean query
        queries.append(normalized_claim)

        # 2. Topic + scientific/factual terms
        if entities:
            ent_str = " ".join(entities[:2])
            queries.append(f"{ent_str} scientific evidence consensus")
        else:
            queries.append(f"{topic} empirical evidence")

        # 3. Refutation / Fact-Check perspective
        if entities:
            queries.append(f"{entities[0]} fact check debunk")
        else:
            queries.append(f"{normalized_claim} fact check")

        # 4. Domain-specific authoritative angle
        if category == ClaimCategory.SCIENCE:
            queries.append(f"{topic} NASA NOAA scientific measurement")
        elif category == ClaimCategory.HEALTH:
            queries.append(f"{topic} clinical trial NIH WHO FDA medical consensus")
        elif category == ClaimCategory.POLITICS:
            queries.append(f"{topic} official record legislation voting record")
        elif category == ClaimCategory.FINANCE:
            queries.append(f"{topic} Federal Reserve official statistics data")
        else:
            queries.append(f"{topic} primary sources verified documentation")

        # Deduplicate while preserving order
        unique_queries = []
        for q in queries:
            cleaned_q = q.strip()
            if cleaned_q and cleaned_q not in unique_queries:
                unique_queries.append(cleaned_q)

        return unique_queries[:4]

    @classmethod
    def analyze(cls, claim: str) -> ClaimAnalysisResult:
        """Executes full claim analysis pipeline."""
        logger.info("Analyzing claim: '%s'", claim[:60])
        normalized = cls.normalize_input(claim)
        category = cls.classify_category(normalized)
        entities = cls.extract_entities(normalized)
        dates = cls.extract_dates(normalized)
        locations = cls.extract_locations(normalized)
        topic = cls.determine_verification_topic(normalized, category, entities)
        queries = cls.generate_search_queries(normalized, category, entities, topic)

        verification_needs = [
            f"Identify authoritative primary documents on {topic}.",
            "Locate peer-reviewed research, empirical measurements, or official records.",
            "Compare supporting arguments against established scientific/historical consensus.",
            "Detect absence of verifiable citations or contradictory empirical evidence.",
        ]

        return ClaimAnalysisResult(
            original_claim=claim,
            normalized_claim=normalized,
            category=category,
            main_assertion=normalized,
            entities=entities,
            dates=dates,
            locations=locations,
            verification_topic=topic,
            search_queries=queries,
            verification_needs=verification_needs,
        )


claim_analyzer = ClaimAnalyzer()
