"""Deadline display card for action plans."""

import streamlit as st


def render_deadline_card(
    date: str,
    description: str,
    consequence_hint: str | None = None,
    urgent: bool = False,
) -> None:
    icon = "🔴" if urgent else "📅"
    with st.container(border=True):
        st.markdown(f"### {icon} {date}")
        st.write(description)
        if consequence_hint:
            st.warning(consequence_hint)
