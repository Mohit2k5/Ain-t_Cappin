from app.utils.source_quality import source_quality_evaluator, SourceQualityEvaluator


def test_domain_extraction():
    assert SourceQualityEvaluator.extract_domain("https://www.nasa.gov/mission_pages/") == "nasa.gov"
    assert SourceQualityEvaluator.extract_domain("http://nature.com:8080/articles") == "nature.com"
    assert SourceQualityEvaluator.extract_domain("https://subdomain.who.int/page") == "subdomain.who.int"


def test_government_source_evaluation():
    assessment = source_quality_evaluator.evaluate(
        url="https://www.cdc.gov/vaccines/safety/index.html",
        title="Vaccine Safety Basics",
        publication_date="2023-10-01",
    )
    assert assessment.domain == "cdc.gov"
    assert assessment.credibility_tier == "High"
    assert assessment.affiliation == "Government"
    assert assessment.is_primary_source_likely is True
    assert assessment.quality_score >= 90.0


def test_academic_source_evaluation():
    assessment = source_quality_evaluator.evaluate(
        url="https://www.nature.com/articles/s41586-024-0001",
        title="Climate Observations",
    )
    assert assessment.domain == "nature.com"
    assert assessment.credibility_tier == "High"
    assert assessment.affiliation == "Academic/Scientific"
    assert assessment.is_primary_source_likely is True
    assert assessment.quality_score >= 88.0


def test_fact_checking_source_evaluation():
    assessment = source_quality_evaluator.evaluate(
        url="https://www.snopes.com/fact-check/earth-shape-measurements/",
        title="Is Earth Flat?",
    )
    assert assessment.domain == "snopes.com"
    assert assessment.credibility_tier == "High"
    assert assessment.affiliation == "Fact-Checking"
    assert assessment.quality_score >= 85.0


def test_social_media_source_evaluation():
    assessment = source_quality_evaluator.evaluate(
        url="https://www.reddit.com/r/conspiracy/comments/12345",
        title="Discussion on topic",
    )
    assert assessment.domain == "reddit.com"
    assert assessment.credibility_tier == "Caution"
    assert assessment.affiliation == "Social / User-Generated"
    assert assessment.quality_score < 50.0


def test_satire_source_evaluation():
    assessment = source_quality_evaluator.evaluate(
        url="https://www.theonion.com/scientists-discover-new-planet",
        title="Parody News",
    )
    assert assessment.domain == "theonion.com"
    assert assessment.credibility_tier == "Low"
    assert assessment.affiliation == "Satire / Known Unreliable"
    assert assessment.quality_score < 30.0


def test_domain_reputation_disclaimer_present():
    assessment = source_quality_evaluator.evaluate(url="https://www.reuters.com/news")
    notes_text = " ".join(assessment.notes).lower()
    assert "domain reputation" in notes_text
    assert "not an absolute guarantee" in notes_text
