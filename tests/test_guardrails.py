from __future__ import annotations

"""
Unit Tests for Phase 5 — Guardrails & Compliance

Tests the guardrail module for PII leakage prevention,
advisory query refusal, off-topic detection, and profanity filtering.
"""

import pytest

from src.pipeline.guardrails import Guardrails


@pytest.fixture
def guardrails() -> Guardrails:
    """Return a Guardrails instance."""
    return Guardrails()


# ───────────────────────────────────────────────────────────
# PII Detection Tests
# ───────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query",
    [
        "My PAN is ABCDE1234F",
        "Here is my PAN: abcde1234f",
        "Aadhaar 1234 5678 9012",
        "Aadhaar 1234-5678-9012",
        "Aadhaar number is 123456789012",
        "Call me at 9876543210",
        "Contact: +91-9876543210",
        "Send details to user@mail.com",
        "My email is test.user+amc@hdfc.co.in",
        "The OTP is 123456",
        "One-time password: 4839",
    ],
)
def test_pii_blocked(guardrails: Guardrails, query: str) -> None:
    """Test that personal identifying information is blocked."""
    result = guardrails.check_query(query)
    assert result is not None
    assert result["status"] == "refused"
    assert result["type"] == "pii"
    assert "personally identifiable information" in result["answer"]
    assert result["citation"] is None
    assert result["educational_link"] is None


# ───────────────────────────────────────────────────────────
# Advisory Query Tests
# ───────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query",
    [
        "Should I invest in HDFC Mid-Cap?",
        "Is it safe to buy HDFC Equity Fund?",
        "Should I sell my mutual funds now?",
        "Which fund gives better returns between mid-cap and large-cap?",
        "Which fund is best for long term?",
        "Recommend me a mutual fund",
        "Suggest a fund to invest in",
        "Give me financial advice on mutual funds",
        "Is this fund safe to invest?",
        "Which fund is good for tax saving?",
        "Best mutual fund under HDFC",
    ],
)
def test_advisory_blocked(guardrails: Guardrails, query: str) -> None:
    """Test that queries asking for advice or recommendations are blocked."""
    result = guardrails.check_query(query)
    assert result is not None
    assert result["status"] == "refused"
    assert result["type"] == "advisory"
    assert "investment advice" in result["answer"]
    assert result["educational_link"] == "https://www.amfiindia.com/investor-corner/knowledge-center"


# ───────────────────────────────────────────────────────────
# Off-Topic / Out-of-Scope Tests
# ───────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query",
    [
        "What's the weather today in Mumbai?",
        "How do I write a binary search in Python?",
        "Who is the Prime Minister of India?",
        "Explain quantum computing",
        "Is ICICI Pru Bluechip fund a good investment?",  # off-topic (unsupported AMC)
        "What are the top holdings of SBI Small Cap?",   # off-topic (unsupported AMC)
    ],
)
def test_off_topic_blocked(guardrails: Guardrails, query: str) -> None:
    """Test that general off-topic queries are blocked."""
    result = guardrails.check_query(query)
    assert result is not None
    assert result["status"] == "refused"
    assert result["type"] == "off_topic"
    assert "only assist with factual queries regarding the 5 supported HDFC" in result["answer"]


# ───────────────────────────────────────────────────────────
# Profanity Tests
# ───────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query",
    [
        "This mutual fund is stupid crap!",
        "Go fuck yourself",
        "Shut up asshole",
    ],
)
def test_profanity_blocked(guardrails: Guardrails, query: str) -> None:
    """Test that profane queries are blocked."""
    result = guardrails.check_query(query)
    assert result is not None
    assert result["status"] == "refused"
    assert result["type"] == "profanity"
    assert "inappropriate language" in result["answer"]


# ───────────────────────────────────────────────────────────
# Factual / On-Topic Passthrough Tests
# ───────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query",
    [
        "What is the expense ratio of HDFC Mid-Cap Fund?",
        "What is the lock-in period for HDFC ELSS Tax Saver?",
        "What is the current NAV of HDFC Large Cap Fund?",
        "Who is the fund manager of HDFC Focused Fund?",
        "What is the exit load for HDFC Equity Fund?",
        "How do I download my capital gains statement from HDFC AMC?",
        "What is the riskometer category of HDFC Large Cap Fund?",
        "What is the AUM of HDFC Mid-Cap Fund?",
        "What are the top holdings of HDFC Focused Fund?",
    ],
)
def test_factual_passthrough(guardrails: Guardrails, query: str) -> None:
    """Test that valid factual queries about the supported funds pass the guardrails."""
    result = guardrails.check_query(query)
    assert result is None
