"""Tests for pipeline normalization and validation (no API key)."""

import pytest

from agents.errors import EmptyInputError, MissingApiKeyError
from agents.pipeline import _normalize_classification, _normalize_extraction, analyze_letter


def test_normalize_extraction_handles_malformed():
    result = _normalize_extraction({"raw": "not json"})
    assert result["deadlines"] == []
    assert result["requested_documents"] == []
    assert "_parse_warning" in result or "deadlines" in result


def test_normalize_extraction_coerces_lists():
    result = _normalize_extraction({
        "deadlines": [{"date": "2025-07-15", "description": "Submit docs"}],
        "requested_documents": "Meldebescheinigung",
        "required_actions": ["Submit by deadline"],
    })
    assert len(result["deadlines"]) == 1
    assert result["requested_documents"] == ["Meldebescheinigung"]


def test_normalize_classification_handles_bad_confidence():
    result = _normalize_classification({"institution": "Jobcenter", "confidence": "high"})
    assert result["confidence"] is None
    assert result["institution"] == "Jobcenter"


def test_analyze_letter_raises_on_empty():
    with pytest.raises(EmptyInputError):
        analyze_letter("   ")


def test_analyze_letter_demo_mode_skips_api(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setattr(
        "agents.pipeline.get_settings",
        lambda: type("S", (), {
            "google_api_key": "",
            "demo_mode": True,
            "demo_fallback_on_quota": True,
        })(),
    )
    result = analyze_letter("Jobcenter Nachforderung JC-2025-001234")
    assert result["institution"] == "Jobcenter"
    assert result["demo_mode"] is True
    assert result["extraction"]["case_number"] == "JC-2025-001234"


def test_analyze_letter_quota_fallback(monkeypatch):
    from agents.errors import QuotaExceededError

    def fake_run_sync(coro):
        coro.close()
        raise QuotaExceededError("429 RESOURCE_EXHAUSTED")

    monkeypatch.setattr("agents.pipeline._run_coro_sync", fake_run_sync)
    monkeypatch.setattr(
        "agents.pipeline.get_settings",
        lambda: type("S", (), {
            "google_api_key": "test-key",
            "demo_mode": False,
            "demo_fallback_on_quota": True,
        })(),
    )
    result = analyze_letter("Jobcenter test")
    assert result["quota_fallback"] is True
    assert result["institution"] == "Jobcenter"


def test_analyze_letter_raises_on_missing_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setattr(
        "agents.pipeline.get_settings",
        lambda: type("S", (), {
            "google_api_key": "",
            "demo_mode": False,
            "demo_fallback_on_quota": True,
        })(),
    )
    with pytest.raises(MissingApiKeyError):
        analyze_letter("Jobcenter test letter")

