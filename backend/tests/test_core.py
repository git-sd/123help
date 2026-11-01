import pytest

from app.models.schemas import Finding, Source, RiskLevel
from app.services.analysis_provider import analyze_listing
from app.services.graph_builder import build_graph
from app.services.risk_engine import assess_listing


def test_payment_request_is_high_risk_and_quotes_trigger():
    report = assess_listing("Pay Rs 999 registration fee to confirm your internship")
    assert report.risk_level is RiskLevel.high
    assert report.fee_detected is True
    assert "registration fee" in report.findings[0].quote.lower()


def test_negated_fee_warning_is_not_flagged():
    report = assess_listing("We never charge any fee from candidates")
    assert report.fee_detected is False
    assert report.risk_level is RiskLevel.low


@pytest.mark.asyncio
async def test_analysis_provider_falls_back_without_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    report = await analyze_listing("Stipend Rs 10,000 per month")
    assert report.risk_level is RiskLevel.low
    assert report.fee_detected is False


def test_graph_connects_job_findings_and_sources():
    graph = build_graph(
        "Acme Labs",
        "Data Analyst",
        "recruiter@acme-labs.example",
        [Finding(title="Recruiter email is consistent", detail="Matches company domain", status="verified")],
        [Source(url="https://acme-labs.example/careers", title="Careers", source_type="web_search")],
    )
    assert {node.node_type for node in graph.nodes} == {"job", "company", "recruiter", "finding", "source"}
    assert len(graph.edges) == 4
