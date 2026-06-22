"""Static analysis fallback for Kaggle demo recording (no Gemini calls)."""

from __future__ import annotations

from typing import Any

from agents.security import get_disclaimer, hash_text, log_analysis_safe, redact_pii


def build_demo_analysis(letter_text: str, *, reason: str = "demo_mode") -> dict[str, Any]:
    """Return a realistic Jobcenter analysis matching the sample letter fixture."""
    redacted_text, pii_found = redact_pii(letter_text.strip())
    text_hash = hash_text(letter_text)

    institution = "Jobcenter"
    letter_type = "Nachforderung (document request)"

    try:
        log_analysis_safe(
            institution=institution,
            letter_type=letter_type,
            pii_redacted=pii_found,
            text_hash=text_hash,
        )
    except Exception:
        pass

    warnings: list[str] = []
    if reason == "demo_mode":
        warnings.append(
            "Demo mode is enabled (DEMO_MODE=true). Gemini/ADK pipeline was skipped."
        )
    elif reason == "quota_exceeded":
        warnings.append(
            "Gemini free-tier quota was exceeded (429 RESOURCE_EXHAUSTED). "
            "Showing the pre-recorded sample analysis instead."
        )

    return {
        "institution": institution,
        "letter_type": letter_type,
        "confidence": 0.92,
        "classification_reasoning": (
            "Letterhead references Jobcenter Berlin-Mitte and the subject "
            "'Nachforderung von Unterlagen' indicates a follow-up document request "
            "for an ongoing Bürgergeld application."
        ),
        "extraction": {
            "deadlines": [
                {
                    "date": "2025-07-15",
                    "description": "Submit all requested documents",
                    "raw_text": "bis zum 15.07.2025",
                },
            ],
            "requested_documents": [
                "Aktuelle Meldebescheinigung",
                "Kontoauszüge der letzten drei Monate",
                "Mietvertrag und Nachweis der Warmmiete",
            ],
            "amounts": [],
            "required_actions": [
                "Submit the listed documents by 15.07.2025",
                "Reference case number JC-2025-001234 in all correspondence",
            ],
            "case_number": "JC-2025-001234",
            "letter_date": "2025-07-01",
        },
        "explanation_en": (
            "The Jobcenter Berlin-Mitte is processing your Bürgergeld application and needs "
            "three documents by **15 July 2025**: a current registration certificate "
            "(Meldebescheinigung), bank statements for the last three months, and your lease "
            "agreement plus proof of warm rent (Warmmiete). If you miss the deadline, your "
            "benefit claim may be suspended under **§ 60 SGB I**. Use case reference "
            "**JC-2025-001234** when you reply or visit the office."
        ),
        "action_checklist": [
            {
                "priority": "urgent",
                "action": "Request Meldebescheinigung from your Bürgeramt (if you do not have a current one)",
                "deadline": "2025-07-15",
            },
            {
                "priority": "urgent",
                "action": "Print or export bank statements for the last three months",
                "deadline": "2025-07-15",
            },
            {
                "priority": "soon",
                "action": "Gather Mietvertrag and proof of Warmmiete (e.g. rent payment receipts)",
                "deadline": "2025-07-15",
            },
            {
                "priority": "soon",
                "action": "Submit all documents to Jobcenter Berlin-Mitte before the deadline",
                "deadline": "2025-07-15",
            },
            {
                "priority": "later",
                "action": "Keep copies of everything you submit and note the submission date",
                "deadline": None,
            },
        ],
        "reply_draft_de": (
            "Betreff: Nachreichung Unterlagen — Aktenzeichen JC-2025-001234\n\n"
            "Sehr geehrte Damen und Herren,\n\n"
            "bezugnehmend auf Ihr Schreiben vom 01.07.2025 (Aktenzeichen JC-2025-001234) "
            "übersende ich Ihnen die angeforderten Unterlagen:\n"
            "1. Aktuelle Meldebescheinigung\n"
            "2. Kontoauszüge der letzten drei Monate\n"
            "3. Mietvertrag und Nachweis der Warmmiete\n\n"
            "Für Rückfragen stehe ich Ihnen gerne zur Verfügung.\n\n"
            "Mit freundlichen Grüßen\n"
            "[NAME]\n"
            "[ADDRESS]"
        ),
        "key_terms_explained": [
            {
                "term": "Nachforderung",
                "meaning_en": "A formal request to submit documents that were missing from your application.",
            },
            {
                "term": "Meldebescheinigung",
                "meaning_en": "Registration certificate from the Bürgeramt confirming your registered address.",
            },
            {
                "term": "Warmmiete",
                "meaning_en": "Rent including utilities (heating, water, etc.), as opposed to Kaltmiete (cold rent).",
            },
            {
                "term": "§ 60 SGB I",
                "meaning_en": "Social law provision allowing benefits to be suspended if required documents are not provided.",
            },
        ],
        "disclaimer": get_disclaimer(),
        "pii_redacted": pii_found,
        "redacted_preview": redacted_text[:500],
        "warnings": warnings,
        "demo_mode": reason == "demo_mode",
        "quota_fallback": reason == "quota_exceeded",
        "analysis_source": reason,
    }
