import os
import sys
import time

import streamlit as st

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from frontend.utils.session import get_state, run_graph, set_state, run_selected_agent, save_current_project
from workflow.router import WorkflowRouter


router = WorkflowRouter()

AGENT_NAME_MAP = {
    "planning": "Planning Agent",
    "literature": "Literature Agent",
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
    for message in state.chat_history:
        with st.chat_message(message.role):
            if message.role == "user":
                st.markdown(f"🧑‍💻 **You**  \n{message.content}")
            else:
                agent_name = message.agent or "Agent"
                st.markdown(f"🤖 **{agent_name}**  \n{message.content}")

    prompt = st.chat_input("Ask ResearchForge to plan, search literature, write manuscript, cite papers, or review work...")
    if prompt:
        state.user_input = prompt
        set_state(state)
        save_current_project(state)

        selected_mode = st.session_state.get("agent_mode", "Smart Router (Recommended)")
        agent_label = _get_display_agent_label(selected_mode, prompt)
        st.session_state.running_agent = agent_label
        st.session_state.last_status = f"Running: {agent_label}"
        st.session_state.last_agent = agent_label
        st.session_state.chat_processing = True
        updated_state = state
        try:
            st.markdown("<div style='margin: 0.5rem 0;'><div class='stSpinner'>⏳ Finding and running agent...</div></div>", unsafe_allow_html=True)
            with st.spinner(f"Routing and running {agent_label}..."):
                if selected_mode == "Manual Agent Selection":
                    updated_state, data = run_selected_agent(state, prompt, st.session_state.get("selected_manual_agent", "Planning Agent"))
                else:
                    updated_state = run_graph(state)
                    data = updated_state.last_response or {}
                time.sleep(0.05)
            set_state(updated_state)
            save_current_project(updated_state)

            actual_agent = (
                getattr(updated_state, "current_agent", "")
                or data.get("agent", "")
                or agent_label
            )
            st.session_state.last_status = f"Completed with {actual_agent}"
            st.session_state.last_agent = actual_agent
            st.session_state.running_agent = ""
            st.session_state.chat_processing = False
            st.success(f"Request completed with {actual_agent}.")
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

    _render_structured_response(get_state())
