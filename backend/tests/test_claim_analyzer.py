import pytest
from app.services.claim_analyzer import claim_analyzer, ClaimAnalyzer
from app.schemas.claim import ClaimCategory


def test_claim_normalization():
    raw = '   #BreakingNews: @NASA announced "evidence of water on Mars"!!!   '
    normalized = ClaimAnalyzer.normalize_input(raw)
    assert normalized == 'BreakingNews: NASA announced "evidence of water on Mars"!!!'

    quoted = '"The Earth is flat."'
    assert ClaimAnalyzer.normalize_input(quoted) == "The Earth is flat."


def test_entity_extraction():
    claim = "NASA and ESA confirmed the James Webb Space Telescope observations of Mars."
    entities = ClaimAnalyzer.extract_entities(claim)
    assert "NASA" in entities
    assert "ESA" in entities
    assert any("James Webb Space Telescope" in e or "Mars" in e for e in entities)


def test_dates_extraction():
    claim = "In 1969, Apollo 11 landed on the Moon, and recently in 2024 new missions were planned."
    dates = ClaimAnalyzer.extract_dates(claim)
    assert "1969" in dates
    assert "2024" in dates
    assert "recently" in dates


def test_locations_extraction():
    claim = "The Great Wall of China is located in China and is visible from Earth orbit."
    locations = ClaimAnalyzer.extract_locations(claim)
    assert "China" in locations
    assert "Earth" in locations


@pytest.mark.parametrize(
    "claim,expected_category",
    [
        ("The Earth is flat and gravity is an illusion.", ClaimCategory.SCIENCE),
        ("Drinking baking soda and lemon water cures cancer.", ClaimCategory.HEALTH),
        ("The President and the Senate passed the new federal legislation.", ClaimCategory.POLITICS),
        ("Ancient Rome fought in the Punic War during the 2nd century BC.", ClaimCategory.HISTORY),
        ("OpenAI released a new artificial intelligence algorithm for robotics.", ClaimCategory.TECHNOLOGY),
        ("The Federal Reserve raised interest rates to control inflation and GDP.", ClaimCategory.FINANCE),
        ("Breaking: a severe earthquake struck the coastline today.", ClaimCategory.CURRENT_EVENTS),
        ("The Eiffel Tower is located in Paris.", ClaimCategory.GENERAL_FACTUAL),
    ],
)
def test_category_classification(claim, expected_category):
    res = claim_analyzer.analyze(claim)
    assert res.category == expected_category


def test_search_queries_generation():
    claim = "The Earth is flat."
    res = claim_analyzer.analyze(claim)
    assert len(res.search_queries) >= 3
    # Verify multi-perspective queries
    query_text = " ".join(res.search_queries).lower()
    assert "earth" in query_text
    assert any(term in query_text for term in ["consensus", "scientific", "fact check", "nasa"])


def test_claim_analyzer_does_not_generate_verdict():
    res = claim_analyzer.analyze("The Moon is made of green cheese.")
    # Ensure ClaimAnalysisResult contains no verdict field
    assert not hasattr(res, "verdict")
    assert not hasattr(res, "final_verdict")
