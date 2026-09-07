import os
import sys

import streamlit as st

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from frontend.utils.session import get_state


STATUS_BADGES = {
    "verified": ("✅", "Verified", "DOI resolves and the metadata matches."),
    "mismatch": ("❌", "Mismatch", "The DOI resolves to a different paper."),
    "unresolved": ("⚠️", "Unresolved", "No DOI, or the DOI is not registered."),
    "unverified": ("❔", "Unverified", "This citation has not been checked."),
}


def _field(verification, name, default=None):
    """Verification arrives as a model live, as a dict from a saved project."""

    if verification is None:
        return default

    if isinstance(verification, dict):
        value = verification.get(name)
    else:
        value = getattr(verification, name, None)

    return default if value is None else value


def render_verification(verification) -> None:
    status = _field(verification, "status", "unverified")

    icon, label, fallback = STATUS_BADGES.get(status, STATUS_BADGES["unverified"])

    st.write(f"**Verification:** {icon} {label}")

    notes = str(_field(verification, "notes", "") or "").strip()
    st.caption(notes or fallback)

    resolved_title = str(_field(verification, "resolved_title", "") or "").strip()
    if status == "mismatch" and resolved_title:
        st.write(f"**DOI actually points to:** {resolved_title}")

    if _field(verification, "doi_resolved", False):
        title_match = _field(verification, "title_match", 0.0) or 0.0
        st.caption(f"Title similarity: {float(title_match):.2f}")

    claim_supported = _field(verification, "claim_supported")
    if claim_supported is not None:
        mark = "✅ supported" if claim_supported else "❌ not supported"
        st.write(f"**Claim support:** {mark}")


# Kept so existing call sites inside this module stay valid.
_render_verification = render_verification


def _summarise(citations) -> None:
    counts = {}
    for citation in citations:
        status = _field(citation.verification, "status", "unverified")
        counts[status] = counts.get(status, 0) + 1

    columns = st.columns(4)
    for column, key in zip(columns, ["verified", "mismatch", "unresolved", "unverified"]):
        icon, label, _ = STATUS_BADGES[key]
        column.metric(f"{icon} {label}", counts.get(key, 0))

    unconfirmed = len(citations) - counts.get("verified", 0)
    if unconfirmed:
        st.warning(
            f"{unconfirmed} of {len(citations)} citation(s) could not be confirmed "
            "against the DOI registry. Check them before using them in a submission."
        )


def render_citations_page() -> None:
    state = get_state()

    st.subheader("Citations")
    if state.citations:
        _summarise(state.citations)

        for index, citation in enumerate(state.citations, start=1):
            status = _field(citation.verification, "status", "unverified")
            icon = STATUS_BADGES.get(status, STATUS_BADGES["unverified"])[0]

            label = f"{icon} {index}. {citation.title or 'Untitled Citation'}"

            with st.expander(label, expanded=False):
                st.write(f"**Authors:** {citation.authors or 'Unknown'}")
                st.write(f"**Year:** {citation.year or 'Unknown'}")
                st.write(f"**DOI:** {citation.doi or 'Unknown'}")
                st.write(f"**Venue:** {citation.venue or 'Unknown'}")

                claim = (getattr(citation, "claim", "") or "").strip()
                if claim:
                    st.write(f"**Cited to support:** {claim}")

                _render_verification(citation.verification)

                st.write("**BibTeX**")
                st.code(citation.bibtex or "No BibTeX available", language="bibtex")
    else:
        st.info("No citations have been generated yet.")
