"""Letter upload widget."""

from __future__ import annotations

from typing import Callable

import streamlit as st

from config.settings import get_settings


def render_upload_widget(
    on_upload: Callable[[str, bytes], None] | None = None,
    key: str = "letter_upload",
) -> tuple[str, bytes] | None:
    settings = get_settings()
    st.caption(
        f"Upload a PDF or text letter (max {settings.max_upload_size_mb} MB, "
        f"{settings.max_pdf_pages} pages)."
    )
    uploaded = st.file_uploader(
        "Official letter",
        type=["pdf", "txt"],
        key=key,
        help="Your document is stored temporarily and may be redacted for privacy.",
    )
    if uploaded is None:
        return None

    content = uploaded.getvalue()
    if on_upload:
        on_upload(uploaded.name, content)
    return uploaded.name, content
