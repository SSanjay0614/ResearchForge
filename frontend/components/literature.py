import os
import sys

import streamlit as st

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from frontend.utils.session import get_state, save_current_project, set_state


def _render_upload() -> None:
    st.divider()
    st.subheader("Analyze Your Own PDF")
    st.caption(
        "Use this when a paper's PDF is behind a paywall or the publisher blocks "
        "automated downloads. The full text is parsed by section and analyzed."
    )

    uploaded = st.file_uploader(
        "Upload a paper (PDF)",
        type=["pdf"],
        key="literature_pdf_upload",
    )

    if not uploaded:
        return

    if not st.button("Analyze uploaded paper", key="literature_pdf_analyze"):
        return

    import os

    from agents.literature_agent import LiteratureAgent
    from models.paper import Paper
    from models.paper_metadata import PaperMetadata

    os.makedirs("data/uploads", exist_ok=True)
    file_path = os.path.join("data", "uploads", os.path.basename(uploaded.name))

    with open(file_path, "wb") as handle:
        handle.write(uploaded.getbuffer())

    state = get_state()

    with st.spinner("Analyzing the uploaded paper..."):
        try:
            agent = LiteratureAgent()
            analysis = agent.analyze_uploaded_pdf(file_path)
        except Exception as exc:
            st.error(f"Could not analyze this PDF: {exc}")
            return

    title = os.path.splitext(os.path.basename(uploaded.name))[0]

    state.papers.append(
        Paper(
            metadata=PaperMetadata(title=title, venue="Uploaded"),
            analysis=analysis,
            is_relevant=True,
            relevance_reason="Uploaded by the user.",
            analysis_depth="full_text",
        )
    )

    set_state(state)
    save_current_project(state)
    st.success(f"Added '{title}' to the project library.")
    st.rerun()



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


DEPTH_LABELS = {
    "full_text": "Analyzed from the full paper text",
    "abstract": "Analyzed from the abstract only",
}


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
            is_relevant = getattr(paper, "is_relevant", True)
            title = metadata.title or "Untitled Paper"
            label = f"{index}. {title}" if is_relevant else f"{index}. {title}  ·  not relevant"
            with st.expander(label, expanded=has_analysis):
                st.write(f"**Authors:** {', '.join(metadata.authors) if metadata.authors else 'Unknown'}")
                st.write(f"**Year:** {metadata.year or 'Unknown'}")
                st.write(f"**Venue:** {metadata.venue or 'Unknown'}")
                st.write(f"**DOI:** {metadata.doi or 'Unknown'}")

                reason = getattr(paper, "relevance_reason", "")
                if not is_relevant and reason:
                    st.caption(f"Judged not relevant: {reason}")

                if metadata.abstract:
                    st.write("**Abstract**")
                    st.write(metadata.abstract)

                if has_analysis:
                    st.divider()
                    depth = DEPTH_LABELS.get(getattr(paper, "analysis_depth", ""), "")
                    st.write("**Paper Analysis**")
                    if depth:
                        st.caption(depth)
                    _render_paper_analysis(paper)
                elif not is_relevant:
                    st.caption("Kept in the library, but not analyzed because it was judged off-topic.")
                else:
                    st.caption("No detailed analysis available for this paper yet.")
    else:
        st.info("No papers have been discovered yet. Ask the system to search the literature.")

    _render_upload()

