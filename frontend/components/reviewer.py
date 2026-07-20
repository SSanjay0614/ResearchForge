import os
import sys

import streamlit as st

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from frontend.utils.session import get_state


def render_reviewer_page() -> None:
    state = get_state()
    outputs = [
        output for output in (state.conversation_outputs or [])
        if output.get("agent") == "Reviewer Agent"
    ]

    if not outputs:
        reviewer_data = state.reviewer_response or {}
        outputs = [reviewer_data] if reviewer_data else []

    st.subheader("Reviewer Responses")
    if outputs:
        for index, data in enumerate(outputs, start=1):
            response = data.get("response", "")
            revision = data.get("manuscript_revision", "")
            if not response and not revision:
                continue

            st.markdown(f"### Review #{index}")
            if response:
                st.markdown(response)
            else:
                st.info("No reviewer response available yet.")

            if revision:
                st.divider()
                st.subheader("Suggested Manuscript Revision")
                st.markdown(revision)
            elif index < len(outputs):
                st.divider()
    else:
        st.info("No reviewer response available yet.")
