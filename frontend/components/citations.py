import os
import sys

import streamlit as st

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from frontend.utils.session import get_state


def render_citations_page() -> None:
    state = get_state()

    st.subheader("Citations")
    if state.citations:
        for index, citation in enumerate(state.citations, start=1):
            with st.expander(f"{index}. {citation.title or 'Untitled Citation'}", expanded=False):
                st.write(f"**Authors:** {citation.authors or 'Unknown'}")
                st.write(f"**Year:** {citation.year or 'Unknown'}")
                st.write(f"**DOI:** {citation.doi or 'Unknown'}")
                st.write(f"**Venue:** {citation.venue or 'Unknown'}")
                st.write("**BibTeX**")
                st.code(citation.bibtex or "No BibTeX available", language="bibtex")
    else:
        st.info("No citations have been generated yet.")
