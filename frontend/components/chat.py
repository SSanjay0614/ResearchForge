import os
import sys

import streamlit as st
import streamlit.components.v1 as components

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from frontend.utils.session import get_state, run_graph, set_state, run_selected_agent, save_current_project, set_pending_checkpoint
from frontend.components.project import render_pre_manuscript_info
from frontend.components.citations import STATUS_BADGES, render_verification
from workflow.router import WorkflowRouter


router = WorkflowRouter()

AGENT_NAME_MAP = {
    "planning": "Planning Agent",
    "literature": "Literature Agent",
    "literature intelligence": "Literature Agent",
    "synthesis": "Literature Synthesis Agent",
    "manuscript": "Manuscript Agent",
    "citation": "Citation Agent",
    "reviewer": "Reviewer Agent",
}


def _citation_field(citation, field: str, default=None):
    """Citations arrive as models from a live run, dicts from a saved project."""

    if isinstance(citation, dict):
        return citation.get(field) or default

    return getattr(citation, field, None) or default


def _verification_of(citation):
    return _citation_field(citation, "verification")


def _verification_status(citation) -> str:
    verification = _verification_of(citation)

    if verification is None:
        return "unverified"

    if isinstance(verification, dict):
        return verification.get("status") or "unverified"

    return getattr(verification, "status", "unverified") or "unverified"


def _render_citation_warning(citations) -> None:
    """Surface unverifiable citations in the chat, not just on the Citations tab.

    A citation that looks fine here and is flagged two tabs away is a citation
    that gets used, so the warning belongs next to the response that produced it.
    """

    if not citations:
        return

    problems = [
        citation
        for citation in citations
        if _verification_status(citation) != "verified"
    ]

    if not problems:
        st.success(f"All {len(citations)} citation(s) verified against the DOI registry.")
        return

    lines = []
    for citation in problems:
        status = _verification_status(citation)
        icon, label, _ = STATUS_BADGES.get(status, STATUS_BADGES["unverified"])
        title = _citation_field(citation, "title", "Untitled Citation")
        lines.append(f"- {icon} **{title}** — {label.lower()}")

    st.warning(
        f"{len(problems)} of {len(citations)} citation(s) could not be confirmed. "
        "Check these before using them:\n\n" + "\n".join(lines)
    )


def _render_structured_response(state) -> None:
    outputs = state.conversation_outputs or []
    if not outputs:
        data = state.last_response or {}
        outputs = [data] if data else []

    latest_output = outputs[-1] if outputs else {}
    response = latest_output.get("response", "")
    if not response:
        return

    agent_name = latest_output.get("agent") or "Agent"
    st.markdown(f"### 🤖 Latest {agent_name} Output")
    st.markdown(
        f"""
        <div class="agent-response-box">
            {response}
        </div>
        """,
        unsafe_allow_html=True
    )

    if latest_output.get("section"):

        st.markdown(
            f"##### 📝 Section: {latest_output['section']}"
        )

    if latest_output.get("latex"):

        with st.expander(
            "Generated LaTeX",
            expanded=True
        ):

            st.code(
                latest_output["latex"],
                language="latex"
            )
        
    if latest_output.get("questions"):
        st.markdown("##### ❓ Follow-up Questions")
        for question in latest_output.get("questions", []):
            st.markdown(f"- {question}")

    if latest_output.get("papers"):
        st.markdown("##### 📄 Discovered Papers")
        for paper_index, paper in enumerate(latest_output.get("papers", []), start=1):
            if hasattr(paper, "metadata"):
                metadata = paper.metadata
                title = getattr(metadata, "title", "Untitled") if metadata else "Untitled"
            elif isinstance(paper, dict):
                metadata = paper.get("metadata") or {}
                title = metadata.get("title", "Untitled") if isinstance(metadata, dict) else getattr(metadata, "title", "Untitled")
            else:
                title = "Untitled"
            st.markdown(f"**{paper_index}.** {title}")

    if latest_output.get("citations"):
        citations = latest_output.get("citations", [])
        st.markdown("##### 📌 Generated Citations")
        _render_citation_warning(citations)

        for citation_index, citation in enumerate(citations, start=1):
            title = _citation_field(citation, "title", "Untitled Citation")
            bibtex = _citation_field(citation, "bibtex", "No BibTeX available")
            status = _verification_status(citation)
            icon = STATUS_BADGES.get(status, STATUS_BADGES["unverified"])[0]

            with st.expander(f"{icon} {citation_index}. {title}", expanded=status != "verified"):
                render_verification(_verification_of(citation))
                st.write("**BibTeX**")
                st.code(bibtex, language="bibtex")

    if latest_output.get("manuscript_revision"):
        st.markdown("##### 📝 Suggested Manuscript Revision")
        st.info(latest_output["manuscript_revision"])


def _render_chat_citations(output: dict, output_index: int) -> None:
    citations = output.get("citations") or []
    if not citations:
        return

    st.markdown("##### 📌 Generated Citations")
    _render_citation_warning(citations)

    for citation_index, citation in enumerate(citations, start=1):
        title = _citation_field(citation, "title", "Untitled Citation")
        authors = _citation_field(citation, "authors", "Unknown")
        year = _citation_field(citation, "year", "Unknown")
        doi = _citation_field(citation, "doi", "Unknown")
        venue = _citation_field(citation, "venue", "Unknown")
        bibtex = _citation_field(citation, "bibtex", "No BibTeX available")
        status = _verification_status(citation)
        icon = STATUS_BADGES.get(status, STATUS_BADGES["unverified"])[0]

        with st.expander(f"{icon} Citation {output_index + 1}.{citation_index}: {title}"):
            st.write(f"**Authors:** {authors}")
            st.write(f"**Year:** {year}")
            st.write(f"**DOI:** {doi}")
            st.write(f"**Venue:** {venue}")
            render_verification(_verification_of(citation))
            st.write("**BibTeX**")
            st.code(bibtex, language="bibtex")


def _normalize_agent_name(agent_name: str) -> str:
    if not agent_name:
        return "Agent"
    return AGENT_NAME_MAP.get(agent_name.lower(), agent_name)


def _get_display_agent_label(selected_mode: str, prompt: str, state=None) -> str:
    if selected_mode == "Manual Agent Selection":
        return st.session_state.get("selected_manual_agent", "Planning Agent")

    # State goes in so the router can honour preconditions. The graph routes
    # again with the same input and state, and that call is served from the
    # router's cache.
    try:
        action = router.route(prompt, state)
        if action and getattr(action, "agent", ""):
            return _normalize_agent_name(action.agent)
    except Exception:
        pass

    return "Router (auto)"


def _render_checkpoint(state) -> None:
    checkpoint = getattr(state, "pending_checkpoint", None) or {}
    checkpoint_type = checkpoint.get("type")
    if checkpoint_type == "pre_manuscript_info":
        original_request = checkpoint.get("original_request", "")
        if render_pre_manuscript_info("chat_checkpoint", checkpoint=True):
            st.session_state.checkpoint_agent = "Manuscript Agent"
            st.session_state.checkpoint_prompt = original_request
            st.rerun()
        return
    if checkpoint_type not in {"planning_review", "literature_review", "synthesis_review"}:
        return

    checkpoint_config = {
        "planning_review": (
            "Planning is ready.",
            "Proceed to Literature Analysis",
            "Discuss/Modify the Plan",
            "Literature Agent",
            "Find relevant papers for the current research plan.",
            "planning_discussion",
        ),
        "literature_review": (
            "Literature results are ready.",
            "Generate Literature Review",
            "Review/Modify the Literature Results",
            "Literature Synthesis Agent",
            "Generate a literature review from the discovered papers.",
            "literature_discussion",
        ),
        "synthesis_review": (
            "The literature review and research gap are ready.",
            "Discuss Research Gap with Planning Agent",
            "Continue in Chat",
            "Planning Agent",
            "Discuss the literature review and research gap, then update the research plan accordingly.",
            "synthesis_discussion",
        ),
    }
    message, proceed_label, discuss_label, proceed_agent, proceed_prompt, discuss_type = checkpoint_config[checkpoint_type]
    discuss_agent = {
        "planning_review": "Planning Agent",
        "literature_review": "Literature Agent",
        "synthesis_review": "Planning Agent",
    }[checkpoint_type]
    st.info(f"{message} Choose a next step, or continue using the chat box below.")
    proceed_col, discuss_col = st.columns(2)
    with proceed_col:
        if st.button(proceed_label, key=f"checkpoint_proceed_{checkpoint_type}"):
            state = set_pending_checkpoint(state, {})
            set_state(state)
            st.session_state.checkpoint_agent = proceed_agent
            st.session_state.checkpoint_prompt = proceed_prompt
            st.rerun()
    with discuss_col:
        if st.button(discuss_label, key=f"checkpoint_discuss_{checkpoint_type}"):
            if checkpoint_type == "synthesis_review":
                state = set_pending_checkpoint(state, {})
            else:
                state = set_pending_checkpoint(state, {"type": discuss_type})
            set_state(state)
            if checkpoint_type != "synthesis_review":
                st.session_state.checkpoint_agent = discuss_agent
            st.rerun()


def _render_scroll_controls(auto_scroll: bool = False) -> None:
    html = """
    <div id="researchforge-chat-bottom"></div>
    <a id="researchforge-scroll-bottom" class="researchforge-scroll-bottom" href="#researchforge-chat-bottom" aria-label="Scroll to latest message" title="Scroll to latest message">↓</a>
    """
    st.markdown(html, unsafe_allow_html=True)

    if not auto_scroll:
        return

    # A finished run reruns the script, which restores the previous scroll
    # position -- usually somewhere above the response that just arrived. Jump
    # to the end so the newest exchange is what the user sees.
    #
    # st.markdown cannot do this: Streamlit strips <script> from markdown HTML.
    # components.html gets its own iframe, so the scroll has to be applied to
    # window.parent, and the retries cover the gap before the new messages are
    # laid out (the page height grows after the iframe first runs).
    components.html(
        """
        <script>
        (function () {
            const doc = window.parent.document;
            let attempts = 0;

            function toBottom() {
                attempts += 1;
                const anchor = doc.getElementById("researchforge-chat-bottom");
                if (anchor && anchor.scrollIntoView) {
                    anchor.scrollIntoView({behavior: "smooth", block: "end"});
                } else {
                    // Streamlit renders the app inside a scrollable container in
                    // some versions and scrolls the window in others.
                    const main = doc.querySelector('section.main')
                        || doc.querySelector('[data-testid="stAppViewContainer"]');
                    if (main) {
                        main.scrollTop = main.scrollHeight;
                    }
                    window.parent.scrollTo(0, doc.body.scrollHeight);
                }
                if (attempts < 6) {
                    window.setTimeout(toBottom, 250);
                }
            }

            window.setTimeout(toBottom, 120);
        })();
        </script>
        """,
        height=0
    )


def render_chat_page() -> None:
    state = get_state()

    st.subheader("Chat Interface")
    st.caption("Use the workspace to plan, search literature, draft the manuscript, cite papers, and review work.")

    agent_options = [
        "Planning Agent",
        "Literature Agent",
        "Literature Synthesis Agent",
        "Manuscript Agent",
        "Citation Agent",
        "Reviewer Agent",
    ]
    st.session_state.setdefault("agent_mode", "Smart Router (Recommended)")
    st.session_state.setdefault("selected_manual_agent", "Planning Agent")

    mode_col, agent_col = st.columns([1, 2])
    with mode_col:
        selected_mode = st.radio(
            "Execution Mode",
            ["Smart Router (Recommended)", "Manual Agent Selection"],
            key="agent_mode",
            horizontal=True,
        )
    with agent_col:
        if selected_mode == "Manual Agent Selection":
            st.selectbox(
                "Select Agent",
                agent_options,
                key="selected_manual_agent",
                help="Used when Manual Agent Selection mode is enabled",
            )

    st.divider()

    # Chat history rendering
    assistant_output_index = 0
    for message in state.chat_history:
        with st.chat_message(message.role):
            if message.role == "user":
                st.markdown(f"🧑‍💻 **You**  \n{message.content}")
            else:
                agent_name = message.agent or "Agent"
                st.markdown(f"🤖 **{agent_name}**  \n{message.content}")
                outputs = state.conversation_outputs or []
                if assistant_output_index < len(outputs):
                    _render_chat_citations(outputs[assistant_output_index], assistant_output_index)
                assistant_output_index += 1

    _render_checkpoint(state)

    prompt = st.chat_input("Ask ResearchForge to plan, search literature, write manuscript, cite papers, or review work...")
    prompt = prompt or st.session_state.pop("checkpoint_prompt", "")
    forced_agent = st.session_state.pop("checkpoint_agent", "")
    if prompt:
        checkpoint_type = (getattr(state, "pending_checkpoint", None) or {}).get("type")
        if checkpoint_type in {"planning_discussion", "literature_discussion", "synthesis_discussion"}:
            prompt = (
                "Discuss and modify the current workflow result based on the user's request. "
                "Use the existing project context, previous response, and follow-up questions.\n\n"
                f"User modification request: {prompt}"
            )
            state = set_pending_checkpoint(state, {})
            forced_agent = forced_agent or {
                "planning_discussion": "Planning Agent",
                "literature_discussion": "Literature Agent",
                "synthesis_discussion": "Planning Agent",
            }[checkpoint_type]

        display_prompt = prompt.split("\n\nUser modification request: ")[-1]
        with st.chat_message("user"):
            st.markdown(f"🧑‍💻 **You**  \n{display_prompt}")

        state.user_input = prompt
        set_state(state)
        save_current_project(state)

        selected_mode = st.session_state.get("agent_mode", "Smart Router (Recommended)")
        agent_label = forced_agent or _get_display_agent_label(selected_mode, prompt, state)
        if (
            agent_label == "Manuscript Agent"
            and not getattr(state, "pre_manuscript_completed", False)
            and not forced_agent
        ):
            state = set_pending_checkpoint(
                state,
                {
                    "type": "pre_manuscript_info",
                    "original_request": prompt,
                },
            )
            set_state(state)
            save_current_project(state)
            st.rerun()

        st.session_state.running_agent = agent_label
        st.session_state.last_status = f"Running: {agent_label}"
        st.session_state.last_agent = agent_label
        st.session_state.chat_processing = True
        updated_state = state
        try:
            with st.chat_message("assistant"):
                st.markdown(f"🤖 **{agent_label}**")
                with st.spinner(f"{agent_label} is working..."):
                    if forced_agent:
                        updated_state, data = run_selected_agent(state, prompt, forced_agent)
                    elif selected_mode == "Manual Agent Selection":
                        updated_state, data = run_selected_agent(state, prompt, st.session_state.get("selected_manual_agent", "Planning Agent"))
                    else:
                        updated_state = run_graph(state)
                        data = updated_state.last_response or {}
            set_state(updated_state)
            save_current_project(updated_state)

            actual_agent = (
                getattr(updated_state, "current_agent", "")
                or data.get("agent", "")
                or agent_label
            )
            checkpoint_after_agent = {
                "Planning Agent": "planning_review",
                "Literature Intelligence Agent": "literature_review",
                "Literature Agent": "literature_review",
                "Literature Synthesis Agent": "synthesis_review",
            }.get(actual_agent)
            if checkpoint_after_agent:
                updated_state = set_pending_checkpoint(updated_state, {"type": checkpoint_after_agent})
                set_state(updated_state)
                save_current_project(updated_state)
            st.session_state.last_status = f"Completed with {actual_agent}"
            st.session_state.last_agent = actual_agent
            st.session_state.running_agent = ""
            st.session_state.chat_processing = False
            st.success(f"Request completed with {actual_agent}.")
            st.session_state.auto_scroll_chat = True
            st.rerun()
        except Exception as exc:
            save_current_project(state)
            st.session_state.last_status = "Error"
            st.session_state.running_agent = ""
            st.session_state.chat_processing = False
            error_message = str(exc)
            if any(token in error_message.lower() for token in ["llama-server", "cuda", "stack-based buffer", "shared object"]):
                st.error(
                    "The local LLM backend failed while generating a response. This is usually caused by the model runtime or GPU setup, not by the chat UI."
                )
            else:
                st.error(f"Execution failed: {exc}")

    if st.session_state.get("running_agent"):
        st.info(f"Running agent: {st.session_state.running_agent}")
    elif st.session_state.get("last_status"):
        agent_name = st.session_state.get("last_agent") or st.session_state.get("last_status")
        st.caption(f"Status: {st.session_state.last_status} | Agent: {agent_name}")

    _render_scroll_controls(st.session_state.pop("auto_scroll_chat", False))

