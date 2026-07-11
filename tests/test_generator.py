from __future__ import annotations

"""
Unit Tests for Phase 4 — Generator Component

Tests LLM client instantiation and error handling using mock classes.
"""

from unittest.mock import MagicMock, patch
import pytest

from src.pipeline.generator import Generator


def test_generator_missing_api_key() -> None:
    """Test that Generator raises ValueError when initialized without API key."""
    with pytest.raises(ValueError):
        # Pass empty key and patch config to ensure no fallback key is used
        with patch("src.pipeline.generator.GROQ_API_KEY", ""):
            Generator(api_key="")


@patch("src.pipeline.generator.ChatGroq")
def test_generator_generation_success(mock_chat_groq: MagicMock) -> None:
    """Test standard generation path on successful API call."""
    mock_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "HDFC Mid-Cap Fund exit load is 1% if redeemed within 1 year."
    mock_instance.invoke.return_value = mock_response
    mock_chat_groq.return_value = mock_instance

    gen = Generator(api_key="mock_key")
    response = gen.generate("You are an assistant.", "What is the exit load?")

    assert response == "HDFC Mid-Cap Fund exit load is 1% if redeemed within 1 year."
    mock_instance.invoke.assert_called_once()


@patch("src.pipeline.generator.ChatGroq")
def test_generator_api_error_handling(mock_chat_groq: MagicMock) -> None:
    """Test that the generator handles LLM call exceptions gracefully."""
    mock_instance = MagicMock()
    mock_instance.invoke.side_effect = Exception("Rate limit exceeded")
    mock_chat_groq.return_value = mock_instance

    gen = Generator(api_key="mock_key")
    response = gen.generate("System rules", "Query content")

    assert "[ERROR] LLM generation failed" in response
