"""Legal disclaimer banner for all Streamlit pages."""

from pathlib import Path

import streamlit as st


def render_disclaimer_banner() -> None:
    disclaimer_path = Path("DISCLAIMER.md")
    if disclaimer_path.exists():
        text = disclaimer_path.read_text(encoding="utf-8")
        english = text.split("## Deutsch")[0].replace("# Legal Disclaimer / Rechtlicher Hinweis", "").strip()
        summary = english.split("\n\n")[1] if "\n\n" in english else english
    else:
        summary = (
            "This tool provides AI-generated summaries only — not legal advice. "
            "Verify all deadlines against your original letter."
        )
    st.info(summary)
