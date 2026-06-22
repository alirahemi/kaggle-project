"""German Bureaucracy AI Agent — Streamlit MVP."""

from __future__ import annotations

import io
import os
from pathlib import Path

import streamlit as st
from pypdf import PdfReader

from agents.errors import (
    BureaucracyAgentError,
    EmptyInputError,
    GeminiApiError,
    MissingApiKeyError,
    PipelineError,
    QuotaExceededError,
)
from agents.pipeline import analyze_letter
from agents.security import get_disclaimer
from config.settings import reload_settings

SAMPLE_LETTER_PATH = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "fixtures"
    / "sample_letters"
    / "jobcenter_nachforderung.txt"
)

INSTITUTION_ICONS = {
    "Jobcenter": "🏢",
    "Ausländerbehörde": "🛂",
    "Finanzamt": "💶",
    "Krankenkasse": "🏥",
    "Other": "📄",
}

st.set_page_config(
    page_title="German Bureaucracy Agent",
    page_icon="📬",
    layout="wide",
)


def _api_key_configured(settings) -> bool:
    key = settings.google_api_key or os.environ.get("GOOGLE_API_KEY", "")
    return bool(key) and not key.startswith("your-")


def _read_pdf(uploaded_file) -> str:
    try:
        reader = PdfReader(io.BytesIO(uploaded_file.read()))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        if not text.strip():
            raise ValueError("No text could be extracted. The PDF may be scanned.")
        return text
    except Exception as exc:
        raise ValueError(f"Could not read PDF: {exc}") from exc


def _format_confidence(conf: float | None) -> str:
    if conf is None:
        return "—"
    try:
        return f"{float(conf):.0%}"
    except (TypeError, ValueError):
        return "—"


def _show_error(exc: Exception) -> None:
    if isinstance(exc, MissingApiKeyError):
        st.error(str(exc))
        st.info("Create a `.env` file in the project root and set `GOOGLE_API_KEY`.")
    elif isinstance(exc, EmptyInputError):
        st.warning(str(exc))
    elif isinstance(exc, QuotaExceededError):
        st.error(str(exc))
        st.info("Wait about a minute and try again.")
    elif isinstance(exc, GeminiApiError):
        st.error(str(exc))
        st.info("Check your key at https://aistudio.google.com/apikey")
    elif isinstance(exc, PipelineError):
        st.error(str(exc))
    elif isinstance(exc, BureaucracyAgentError):
        st.error(str(exc))
    else:
        st.error(f"Unexpected error: {exc}")


def _render_deadlines(deadlines: list) -> None:
    if not deadlines:
        st.info("No deadlines were detected.")
        return
    for i, item in enumerate(deadlines, 1):
        if not isinstance(item, dict):
            st.markdown(f"{i}. {item}")
            continue
        date = item.get("date") or "Date not parsed"
        desc = item.get("description") or item.get("raw_text") or "Deadline"
        st.markdown(f"**{i}. {date}** — {desc}")


def _render_documents(documents: list) -> None:
    if not documents:
        st.info("No documents were listed.")
        return
    for doc in documents:
        st.markdown(f"- {doc}")


def _render_checklist(items: list) -> None:
    if not items:
        st.info("No action items were generated.")
        return
    for i, item in enumerate(items, 1):
        if isinstance(item, dict):
            priority = item.get("priority", "")
            action = item.get("action", str(item))
            deadline = item.get("deadline")
            icon = {"urgent": "🔴", "soon": "🟡", "later": "🟢"}.get(priority, "⚪")
            line = f"{icon} **{action}**"
            if deadline:
                line += f" *(by {deadline})*"
            st.markdown(f"{i}. {line}")
        else:
            st.markdown(f"{i}. {item}")


def _render_results(result: dict) -> None:
    institution = result.get("institution", "Other")
    icon = INSTITUTION_ICONS.get(institution, "📄")

    st.markdown(f"## {icon} Institution: {institution}")
    st.caption(
        f"Letter type: **{result.get('letter_type', 'Unknown')}** · "
        f"Confidence: **{_format_confidence(result.get('confidence'))}**"
    )

    if result.get("classification_reasoning"):
        st.caption(result["classification_reasoning"])

    if result.get("pii_redacted"):
        st.success("Personal data was redacted before analysis and logging.")

    for warning in result.get("warnings", []):
        st.warning(warning)

    st.divider()
    st.subheader("Summary")
    explanation = result.get("explanation_en", "").strip()
    if explanation:
        st.write(explanation)
    else:
        st.info("No summary was generated. Please try again.")

    terms = result.get("key_terms_explained", [])
    if terms:
        with st.expander("Key German terms"):
            for t in terms:
                if isinstance(t, dict):
                    st.markdown(f"- **{t.get('term', '')}**: {t.get('meaning_en', '')}")

    extraction = result.get("extraction", {})

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Deadlines")
        _render_deadlines(extraction.get("deadlines", []))
    with col_b:
        st.subheader("Required documents")
        _render_documents(extraction.get("requested_documents", []))

    actions = extraction.get("required_actions", [])
    if actions:
        st.subheader("Required actions (from letter)")
        for a in actions:
            st.markdown(f"- {a}")

    st.divider()
    st.subheader("Action checklist")
    _render_checklist(result.get("action_checklist", []))

    st.divider()
    st.subheader("Draft reply (German)")
    reply = result.get("reply_draft_de", "").strip()
    if reply:
        st.text_area(
            "Adapt this draft before sending. Replace [NAME] and [ADDRESS].",
            value=reply,
            height=220,
            label_visibility="collapsed",
        )
    else:
        st.info("No reply draft was generated.")

    with st.expander("Technical details (for judges)"):
        st.markdown(
            "- **Orchestrator:** Google ADK `SequentialAgent`\n"
            "- **Agents:** classifier → extraction → response_writer\n"
            "- **Models:** Gemini 2.5 Flash + Pro\n"
            "- **MCP tools:** `glossary_lookup`, `deadline_calculator`"
        )
        if extraction:
            st.json(extraction)

    with st.expander("Redacted preview"):
        st.text(result.get("redacted_preview", ""))

    st.divider()
    st.warning(result.get("disclaimer", get_disclaimer()))


def main() -> None:
    settings = reload_settings()

    st.title("German Bureaucracy AI Agent")
    st.caption(
        "Understand official letters from Jobcenter, Finanzamt, Ausländerbehörde, and Krankenkasse"
    )

    with st.sidebar:
        if st.button("Load sample Jobcenter letter", use_container_width=True):
            if SAMPLE_LETTER_PATH.exists():
                st.session_state.letter_input = SAMPLE_LETTER_PATH.read_text(encoding="utf-8")
                st.session_state.result = None
                st.session_state.last_analysis_error = None
                st.success("Sample letter loaded.")
            else:
                st.error("Sample letter file not found.")

        st.divider()
        if _api_key_configured(settings):
            st.success("API key configured")
        else:
            st.error("Set GOOGLE_API_KEY in `.env`")

        st.markdown(
            "**Agent pipeline**\n"
            "1. Classifier\n"
            "2. Extraction\n"
            "3. Response writer\n\n"
            "**MCP tools**\n"
            "`glossary_lookup` · `deadline_calculator`"
        )

    if "letter_input" not in st.session_state:
        st.session_state.letter_input = ""

    tab_paste, tab_upload = st.tabs(["Paste text", "Upload PDF"])

    pasted_text = ""
    uploaded_text = ""

    with tab_paste:
        pasted_text = st.text_area(
            "German official letter",
            height=300,
            key="letter_input",
            placeholder="Paste a letter from Jobcenter, Finanzamt, Ausländerbehörde, or Krankenkasse…",
        )

    with tab_upload:
        uploaded = st.file_uploader("PDF letter", type=["pdf"])
        if uploaded is not None:
            try:
                uploaded_text = _read_pdf(uploaded)
                st.text_area("Extracted text", uploaded_text, height=180, disabled=True)
            except ValueError as exc:
                st.error(str(exc))

    letter_text = uploaded_text.strip() if uploaded_text.strip() else pasted_text.strip()

    if st.button("Analyze letter", type="primary", use_container_width=True):
        if not _api_key_configured(settings):
            st.session_state.result = None
            st.session_state.last_analysis_error = MissingApiKeyError(
                "GOOGLE_API_KEY is not set. Create a `.env` file and add your key."
            )
            return
        if not letter_text:
            st.session_state.result = None
            st.session_state.last_analysis_error = EmptyInputError(
                "Paste or upload a letter first."
            )
            return

        with st.spinner("Analyzing… (classify → extract → respond)"):
            try:
                st.session_state.last_analysis_error = None
                st.session_state.result = analyze_letter(letter_text, settings=settings)
            except BureaucracyAgentError as exc:
                st.session_state.result = None
                st.session_state.last_analysis_error = exc
            except Exception as exc:
                st.session_state.result = None
                st.session_state.last_analysis_error = exc

    last_error = st.session_state.get("last_analysis_error")
    if last_error and not st.session_state.get("result"):
        _show_error(last_error)

    result = st.session_state.get("result")
    if result:
        _render_results(result)
    else:
        st.info("Paste a letter or load the sample, then click **Analyze letter**.")


if __name__ == "__main__":
    main()
