import re
import os
import streamlit as st

from memory.state import ProjectState
from storage.project_storage import ProjectStorage
from workflow.graph import graph

from agents.planning_agent import PlanningAgent
from agents.literature_agent import LiteratureAgent
from agents.synthesis_agent import SynthesisAgent
from agents.manuscript_agent import ManuscriptAgent
from agents.citation_agent import CitationAgent
from agents.reviewer_agent import ReviewerAgent

from models.chat_message import ChatMessage
from models.workflow_event import WorkflowEvent


def get_storage() -> ProjectStorage:
    if "storage" not in st.session_state:
        # Resolve to root projects/ folder
        frontend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        root_dir = os.path.dirname(frontend_dir)
        projects_dir = os.path.join(root_dir, "projects")
        st.session_state.storage = ProjectStorage(project_dir=projects_dir)
    return st.session_state.storage


def get_state() -> ProjectState:
    if "project_state" not in st.session_state:
        st.session_state.project_state = ProjectState()
    return st.session_state.project_state


def set_state(state: ProjectState) -> None:
    st.session_state.project_state = state


def save_current_project(state=None, project_id=None) -> None:
    current_state = state or get_state()
    storage = get_storage()
    resolved_project_id = project_id or getattr(current_state, "project_name", "") or getattr(current_state, "topic", "") or "untitled"
    storage.save(current_state, slugify(resolved_project_id))


def get_agent_registry():
    if "agent_registry" not in st.session_state:
        st.session_state.agent_registry = {
            "Planning Agent": PlanningAgent(),
            "Literature Agent": LiteratureAgent(),
            "Literature Synthesis Agent": SynthesisAgent(),
            "Manuscript Agent": ManuscriptAgent(),
            "Citation Agent": CitationAgent(),
            "Reviewer Agent": ReviewerAgent(),
        }
    return st.session_state.agent_registry


def slugify(value: str) -> str:
    slug = re.sub(r"[^0-9A-Za-z._-]+", "_", value or "untitled").strip("_")
    return slug or "untitled"


def inject_custom_css() -> None:
    css_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "style.css"))
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def post_process_agent_run(state: ProjectState, user_input: str, agent_name: str, data: dict, old_history_len: int) -> None:
    """Ensures chat history and conversation outputs are filled correctly, especially

    for agents that completely override the default BaseAgent.run logic.
    """
    # 1. Update last response metadata
    data["agent"] = agent_name
    state.last_response = data

    # 2. Check if chat history was updated
    if len(state.chat_history) <= old_history_len:
        # User message
        state.chat_history.append(
            ChatMessage(
                role="user",
                content=user_input
            )
        )
        # Assistant message
        response_content = data.get("response") or f"I have processed your request as {agent_name}."
        state.chat_history.append(
            ChatMessage(
                role="assistant",
                agent=agent_name,
                content=response_content
            )
        )

    # 3. Ensure conversation outputs list has the latest execution
    output_exists = False
    response_content = data.get("response") or ""
    if state.conversation_outputs:
        latest = state.conversation_outputs[-1]
        if latest.get("agent") == agent_name and latest.get("response") == response_content:
            output_exists = True

    if not output_exists:
        state.conversation_outputs.append(
        {
            "agent": agent_name,

            "response": response_content,

            "questions": data.get("questions", []),

            "papers": data.get("papers", []),

            "citations": data.get("citations", []),

            "manuscript_revision": data.get("manuscript_revision", ""),

            "section": data.get("section", ""),

            "latex": data.get("latex", "")
        }
        )

    # 4. Append a workflow event if not present
    workflow_exists = False
    if state.workflow_history:
        latest_wf = state.workflow_history[-1]
        if latest_wf.agent == agent_name and latest_wf.action == "Completed":
            workflow_exists = True
    if not workflow_exists:
        state.workflow_history.append(
            WorkflowEvent(
                agent=agent_name,
                action="Completed"
            )
        )


def run_graph(state: ProjectState) -> ProjectState:
    state.user_input = state.user_input.strip()
    if not state.user_input:
        return state

    old_history_len = len(state.chat_history)
    result = graph.invoke(state)

    if isinstance(result, ProjectState):
        res_state = result
    elif isinstance(result, dict):
        res_state = ProjectState(**result)
    else:
        res_state = state

    # Post process graph execution
    data = res_state.last_response or {}
    agent_name = data.get("agent") or res_state.current_agent or "Smart Router"
    post_process_agent_run(res_state, state.user_input, agent_name, data, old_history_len)

    return res_state


def run_selected_agent(state: ProjectState, user_input: str, agent_name: str):
    agent = get_agent_registry()[agent_name]
    old_history_len = len(state.chat_history)
    
    updated_state, data = agent.run(state, user_input)
    
    post_process_agent_run(updated_state, user_input, agent.name, data, old_history_len)
    return updated_state, data


def reset_workspace() -> None:
    st.session_state.workspace_ready = False
    st.session_state.project_state = ProjectState()
    st.session_state.running_agent = ""
    st.session_state.last_status = ""

