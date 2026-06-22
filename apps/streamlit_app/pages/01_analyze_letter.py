"""Analyze an uploaded official letter."""

import json

import streamlit as st

from apps.streamlit_app.client.api_client import ApiClient, ApiClientError
from apps.streamlit_app.components.disclaimer_banner import render_disclaimer_banner
from apps.streamlit_app.components.upload import render_upload_widget
from config.settings import get_settings

st.set_page_config(page_title="Analyze Letter", page_icon="📄", layout="wide")
render_disclaimer_banner()
st.title("Analyze Letter")

settings = get_settings()
token = st.session_state.get("api_token")
client = ApiClient(token=token)

if not token:
    st.error("API token missing. Open the home page first or start the API gateway.")
    st.stop()

col1, col2 = st.columns([1, 1])
with col1:
    locale = st.selectbox("Explanation language", ["en", "de"], index=0)
    bundesland = st.selectbox("Bundesland", ["BE", "BY", "NW", "HH", "HE"], index=0)

with col2:
    if st.button("Create session", type="primary"):
        try:
            session = client.create_session(locale=locale, bundesland=bundesland)
            st.session_state.session_id = session["session_id"]
            st.success(f"Session created: {session['session_id']}")
        except ApiClientError as exc:
            st.error(exc.message)

uploaded = render_upload_widget(key="analyze_upload")
if uploaded and st.session_state.get("session_id"):
    filename, content = uploaded
    if st.button("Upload & analyze", type="primary"):
        with st.spinner("Uploading and analyzing…"):
            try:
                doc = client.upload_document(st.session_state.session_id, filename, content)
                st.session_state.document_id = doc["document_id"]
                status = client.start_analysis(st.session_state.session_id, doc["document_id"])
                st.session_state.analysis_id = status["analysis_id"]
                result = client.get_analysis(status["analysis_id"])
                st.session_state.analysis_result = result
                st.success("Analysis complete")
            except ApiClientError as exc:
                st.error(exc.message)

if result := st.session_state.get("analysis_result"):
    st.subheader("Summary")
    explanation = result.get("explanation") or {}
    st.write(explanation.get("summary", "No summary available."))
    if extraction := result.get("extraction"):
        st.subheader("Extracted deadlines")
        for item in extraction.get("deadlines", []):
            st.markdown(f"- **{item['date']}**: {item['description']}")
    with st.expander("Full JSON"):
        st.code(json.dumps(result, indent=2), language="json")
