import os
import sys

import streamlit as st

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from frontend.utils.session import get_state, run_graph, set_state, run_selected_agent, save_current_project, set_pending_checkpoint
from frontend.components.project import render_pre_manuscript_info
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
        st.markdown("##### 📌 Generated Citations")
        for citation_index, citation in enumerate(latest_output.get("citations", []), start=1):
            if isinstance(citation, dict):
                title = citation.get("title") or "Untitled Citation"
                bibtex = citation.get("bibtex") or "No BibTeX available"
            else:
                title = getattr(citation, "title", "Untitled Citation")
                bibtex = getattr(citation, "bibtex", "No BibTeX available")
                
            with st.expander(f"📌 {citation_index}. {title}", expanded=False):
                st.write(f"**BibTeX**")
                st.code(bibtex, language="bibtex")

    if latest_output.get("manuscript_revision"):
        st.markdown("##### 📝 Suggested Manuscript Revision")
        st.info(latest_output["manuscript_revision"])


def _render_chat_citations(output: dict, output_index: int) -> None:
    citations = output.get("citations") or []
    if not citations:
        return

    st.markdown("##### 📌 Generated Citations")
    for citation_index, citation in enumerate(citations, start=1):
        if isinstance(citation, dict):
            title = citation.get("title") or "Untitled Citation"
            authors = citation.get("authors") or "Unknown"
            year = citation.get("year") or "Unknown"
            doi = citation.get("doi") or "Unknown"
            venue = citation.get("venue") or "Unknown"
            bibtex = citation.get("bibtex") or "No BibTeX available"
        else:
            title = getattr(citation, "title", "Untitled Citation")
            authors = getattr(citation, "authors", None) or "Unknown"
            year = getattr(citation, "year", None) or "Unknown"
            doi = getattr(citation, "doi", None) or "Unknown"
            venue = getattr(citation, "venue", None) or "Unknown"
            bibtex = getattr(citation, "bibtex", None) or "No BibTeX available"

        with st.expander(f"📌 Citation {output_index + 1}.{citation_index}: {title}"):
            st.write(f"**Authors:** {authors}")
            st.write(f"**Year:** {year}")
            st.write(f"**DOI:** {doi}")
            st.write(f"**Venue:** {venue}")
            st.write("**BibTeX**")
            st.code(bibtex, language="bibtex")


def _normalize_agent_name(agent_name: str) -> str:
    if not agent_name:
        return "Agent"
    return AGENT_NAME_MAP.get(agent_name.lower(), agent_name)


def _get_display_agent_label(selected_mode: str, prompt: str) -> str:
    if selected_mode == "Manual Agent Selection":
        return st.session_state.get("selected_manual_agent", "Planning Agent")

    try:
        action = router.route(prompt)
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
    html = f"""
    <div id="researchforge-chat-bottom"></div>
    <a id="researchforge-scroll-bottom" class="researchforge-scroll-bottom" href="#researchforge-chat-bottom" aria-label="Scroll to latest message" title="Scroll to latest message">↓</a>
    """
    st.markdown(html, unsafe_allow_html=True)


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
        agent_label = forced_agent or _get_display_agent_label(selected_mode, prompt)
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

