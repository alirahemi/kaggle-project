"""Legal disclaimer banner for all Streamlit pages."""

from pathlib import Path

import streamlit as st

DEFAULT_DISCLAIMER = (
    "This tool provides AI-generated summaries only — not legal advice. "
    "Verify all deadlines and obligations against your original letter and "
    "consult a qualified advisor or the issuing authority."
)


def _read_disclaimer_file(path: Path) -> str:
    """Read disclaimer text: UTF-8 first, then cp1252 fallback."""
    raw = path.read_bytes()
    for encoding in ("utf-8", "cp1252"):
        try:
            text = raw.decode(encoding)
            # Reject mis-decoded UTF-16 (null bytes between ASCII characters).
            if "\x00" in text:
                continue
            return text
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError(
        "disclaimer",
        raw,
        0,
        1,
        "Could not decode DISCLAIMER.md as utf-8 or cp1252",
    )


def _extract_english_summary(text: str) -> str:
    """Pull a short English summary from DISCLAIMER.md content."""
    english = text.split("## Deutsch")[0]
    english = english.replace("# Legal Disclaimer / Rechtlicher Hinweis", "").strip()
    english = english.replace("## English", "").strip()
    if "\n\n" in english:
        return english.split("\n\n")[0].strip()
    return english.strip()


def load_disclaimer_summary() -> str:
    """Load disclaimer summary without raising on encoding or I/O errors."""
    disclaimer_path = Path("DISCLAIMER.md")
    if not disclaimer_path.exists():
        return DEFAULT_DISCLAIMER

    try:
        text = _read_disclaimer_file(disclaimer_path)
        summary = _extract_english_summary(text)
        return summary if summary else DEFAULT_DISCLAIMER
    except Exception:
        return DEFAULT_DISCLAIMER


def render_disclaimer_banner() -> None:
    """Render the legal disclaimer banner; never crashes the page."""
    try:
        summary = load_disclaimer_summary()
    except Exception:
        summary = DEFAULT_DISCLAIMER
    st.info(summary)
