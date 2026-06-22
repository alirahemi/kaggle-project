"""Concierge follow-up chat."""

import streamlit as st

from apps.streamlit_app.client.api_client import ApiClient, ApiClientError
from apps.streamlit_app.components.disclaimer_banner import render_disclaimer_banner

st.set_page_config(page_title="Ask Concierge", page_icon="💬", layout="wide")
render_disclaimer_banner()
st.title("Ask Concierge")

token = st.session_state.get("api_token")
session_id = st.session_state.get("session_id")

if not token:
    st.error("API token missing.")
    st.stop()
if not session_id:
    st.info("Create a session on the home page or Analyze Letter page.")
    st.stop()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

client = ApiClient(token=token)

for entry in st.session_state.chat_history:
    with st.chat_message(entry["role"]):
        st.write(entry["content"])
        if entry.get("disclaimer"):
            st.caption(entry["disclaimer"])

prompt = st.chat_input("Ask about your letter, deadlines, or next steps…")
if prompt:
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    try:
        response = client.chat(session_id, prompt)
        assistant_text = response["response"]
        disclaimer = response.get("disclaimer", "")
        st.session_state.chat_history.append(
            {"role": "assistant", "content": assistant_text, "disclaimer": disclaimer}
        )
        with st.chat_message("assistant"):
            st.write(assistant_text)
            if sources := response.get("sources"):
                st.caption(f"Sources: {', '.join(sources)}")
            st.caption(disclaimer)
    except ApiClientError as exc:
        st.error(exc.message)
