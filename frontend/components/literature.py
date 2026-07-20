import os
import sys

import streamlit as st

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from frontend.utils.session import get_state


def _paper_has_analysis(paper) -> bool:
    analysis = getattr(paper, "analysis", None)
    if not analysis:
        return False

    for field_name in [
        "contribution",
        "problem_statement",
        "methodology",
        "results",
        "limitations",
        "future_work",
        "strengths",
        "weaknesses",
        "keywords",
        "important_findings",
    ]:
        value = getattr(analysis, field_name, None)
        if isinstance(value, list):
            if value:
                return True
        elif value:
            return True

    return False


def _render_paper_analysis(paper) -> None:
    analysis = getattr(paper, "analysis", None)
    if not analysis:
        return

    sections = [
        ("Contribution", getattr(analysis, "contribution", "")),
        ("Problem Statement", getattr(analysis, "problem_statement", "")),
        ("Methodology", getattr(analysis, "methodology", "")),
        ("Results", getattr(analysis, "results", "")),
        ("Limitations", getattr(analysis, "limitations", "")),
        ("Future Work", getattr(analysis, "future_work", "")),
    ]

    for title, value in sections:
        if value:
            st.write(f"**{title}:**")
            st.write(value)

    for field_name, title in [("datasets", "Datasets"), ("evaluation_metrics", "Evaluation Metrics"), ("strengths", "Strengths"), ("weaknesses", "Weaknesses"), ("keywords", "Keywords"), ("important_findings", "Important Findings")]:
        values = getattr(analysis, field_name, None) or []
        if values:
            st.write(f"**{title}:**")
            for item in values:
                st.write(f"- {item}")


def render_literature_page() -> None:
    state = get_state()

    st.subheader("Discovered Papers")
    if state.papers:
        papers_with_analysis = [paper for paper in state.papers if _paper_has_analysis(paper)]
        papers_without_analysis = [paper for paper in state.papers if not _paper_has_analysis(paper)]
        display_papers = papers_with_analysis + papers_without_analysis

        for index, paper in enumerate(display_papers, start=1):
            metadata = paper.metadata
            has_analysis = _paper_has_analysis(paper)
            with st.expander(f"{index}. {metadata.title or 'Untitled Paper'}", expanded=has_analysis):
                st.write(f"**Authors:** {', '.join(metadata.authors) if metadata.authors else 'Unknown'}")
                st.write(f"**Year:** {metadata.year or 'Unknown'}")
                st.write(f"**Venue:** {metadata.venue or 'Unknown'}")
                st.write(f"**DOI:** {metadata.doi or 'Unknown'}")
                if metadata.abstract:
                    st.write("**Abstract**")
                    st.write(metadata.abstract)

                if has_analysis:
                    st.divider()
                    st.write("**Paper Analysis**")
                    _render_paper_analysis(paper)
                else:
                    st.caption("No detailed analysis available for this paper yet.")
    else:
        st.info("No papers have been discovered yet. Ask the system to search the literature.")
