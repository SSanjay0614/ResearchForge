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

    st.subheader("📝 Reviewer Responses & Rebuttals")
    if outputs:
        for index, data in enumerate(outputs, start=1):
            comment = data.get("reviewer_comment", "")
            response = data.get("response", "")
            revision = data.get("manuscript_revision", "")
            if not response and not revision and not comment:
                continue

            with st.container(border=True):
                st.markdown(f"### Review #{index}")
                
                if comment:
                    st.markdown("**🔍 Reviewer Comment / Prompt:**")
                    st.info(comment)

                if response:
                    st.markdown("**💬 Author Response:**")
                    st.markdown(response)

                if revision:
                    st.markdown("**📄 Suggested Manuscript Revision:**")
                    st.code(revision, language="latex")
    else:
        st.info("No reviewer responses generated yet. Ask the Reviewer Agent to respond to a comment in the chat tab!")

