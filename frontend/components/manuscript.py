import os
import sys

import streamlit as st

from frontend.utils.session import set_state

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from frontend.utils.session import get_state


SECTION_FIELDS = {
    "title": "Title",
    "abstract": "Abstract",
    "introduction": "Introduction",
    "literature_review": "Literature Review",
    "methodology": "Methodology",
    "experiments": "Experiments",
    "results": "Results",
    "discussion": "Discussion",
    "conclusion": "Conclusion",
}


def _build_latex_source_from_state(state) -> str:
    manuscript = state.manuscript
    sections = []

    for field_name in [
        "title",
        "abstract",
        "introduction",
        "literature_review",
        "methodology",
        "experiments",
        "results",
        "discussion",
        "conclusion",
    ]:
        value = getattr(manuscript, field_name, "") or ""
        if value.strip():
            sections.append(value)

    for section_name, content in (getattr(manuscript, "sections", {}) or {}).items():
        if content and str(content).strip():
            sections.append(f"\\section{{{section_name}}}\n\n{content}")

    return "\n\n".join(sections)


def render_manuscript_page() -> None:
    state = get_state()
    manuscript = state.manuscript

    st.subheader("Manuscript Sections")
    st.caption("Edit the generated sections directly. The current state is passed back to the backend on the next request.")

    for key, label in SECTION_FIELDS.items():
        value = getattr(manuscript, key, "") or ""
        session_key = f"manuscript_{key}"
        
        # Synchronize with backend manuscript object
        if session_key not in st.session_state or st.session_state[session_key] != value:
            st.session_state[session_key] = value

        is_expanded = key in ["title", "abstract"]
        with st.expander(f"📝 {label}", expanded=is_expanded):
            updated_value = st.text_area(
                f"Edit {label}",
                height=180,
                key=session_key,
                label_visibility="collapsed"
            )
            setattr(manuscript, key, updated_value)

    custom_sections = getattr(manuscript, "sections", {}) or {}
    if custom_sections:
        st.divider()
        st.subheader("Custom Sections")
        for section_name, section_content in list(custom_sections.items()):
            session_key = f"custom_section_{section_name}"
            value = section_content or ""
            
            # Synchronize with backend manuscript object
            if session_key not in st.session_state or st.session_state[session_key] != value:
                st.session_state[session_key] = value

            with st.expander(f"➕ {section_name.replace('_', ' ').title()}", expanded=True):
                updated_value = st.text_area(
                    section_name.replace("_", " ").title(),
                    height=180,
                    key=session_key,
                    label_visibility="collapsed"
                )
                manuscript.sections[section_name] = updated_value

    state.manuscript.latex_source = _build_latex_source_from_state(state)

    if state.manuscript.latex_source:
        st.divider()
        st.subheader("LaTeX Source")
        st.code(state.manuscript.latex_source, language="latex")

    set_state(state)
