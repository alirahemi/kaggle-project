"""Action plan dashboard from the latest analysis."""

import streamlit as st

from apps.streamlit_app.client.api_client import ApiClient, ApiClientError
from apps.streamlit_app.components.deadline_card import render_deadline_card
from apps.streamlit_app.components.disclaimer_banner import render_disclaimer_banner

st.set_page_config(page_title="Action Plan", page_icon="✅", layout="wide")
render_disclaimer_banner()
st.title("Action Plan")

analysis_id = st.session_state.get("analysis_id")
token = st.session_state.get("api_token")

if not analysis_id or not token:
    st.info("Run an analysis on the **Analyze Letter** page first.")
    st.stop()

client = ApiClient(token=token)
try:
    result = client.get_analysis(analysis_id)
except ApiClientError as exc:
    st.error(exc.message)
    st.stop()

plan = result.get("action_plan") or {}
sections = [
    ("Urgent", plan.get("urgent", []), True),
    ("This week", plan.get("this_week", []), False),
    ("Later", plan.get("later", []), False),
    ("Optional", plan.get("optional", []), False),
]

for title, items, urgent in sections:
    if not items:
        continue
    st.subheader(title)
    for item in items:
        deadline = item.get("deadline")
        if deadline:
            render_deadline_card(
                date=deadline,
                description=item["action"],
                urgent=urgent,
            )
        else:
            st.markdown(f"- {item['action']}")
        if item.get("form_url"):
            st.link_button("Open form", item["form_url"])

extraction = result.get("extraction") or {}
if deadlines := extraction.get("deadlines"):
    st.divider()
    st.subheader("Letter deadlines")
    for d in deadlines:
        render_deadline_card(
            date=d["date"],
            description=d["description"],
            consequence_hint=d.get("consequence_hint"),
            urgent=True,
        )
