import os
import sys

import streamlit as st

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from frontend.utils.session import get_state


def render_literature_review_page() -> None:
    state = get_state()

    literature_review = state.literature_review
    research_gap = state.research_gap

    st.subheader("Literature Review")
    if literature_review:
        st.markdown(literature_review)
    else:
        st.info("No literature review generated yet. Ask the system to synthesize the current literature.")

    st.divider()
    st.subheader("Research Gap")
    if research_gap:
        st.markdown(research_gap)
    else:
        st.info("No research gap identified yet.")
