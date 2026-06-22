"""Privacy settings and GDPR data controls."""

import streamlit as st

from apps.streamlit_app.components.disclaimer_banner import render_disclaimer_banner
from config.settings import get_settings

st.set_page_config(page_title="Privacy Settings", page_icon="🔒", layout="wide")
render_disclaimer_banner()
st.title("Privacy & GDPR Settings")

settings = get_settings()

st.subheader("Data handling")
st.markdown(
    f"""
- **Retention**: uploaded documents are deleted after **{settings.document_retention_days} days**.
- **PII redaction**: {"enabled" if settings.pii_redaction_enabled else "disabled"} for previews.
- **Max upload size**: {settings.max_upload_size_mb} MB
- **Storage backend**: `{settings.storage_backend}`
"""
)

st.subheader("Your rights")
st.markdown(
    """
Under GDPR you may request a copy of your data or ask for deletion.
Use the buttons below when the API gateway is running with your account token.
"""
)

col1, col2 = st.columns(2)
with col1:
    if st.button("Export my data"):
        st.info("Export requested — check API response for download link (demo stub).")
with col2:
    confirm = st.checkbox("I understand this permanently deletes my sessions and documents.")
    if st.button("Delete my data", type="primary", disabled=not confirm):
        st.warning("Deletion requested — demo stub returns success with zero records removed.")

st.divider()
st.caption("For production deployments, audit logs are written via the audit MCP server.")
