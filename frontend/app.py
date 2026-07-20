import os
import sys

# Reconfigure stdout/stderr to use UTF-8 on Windows to avoid console print charmap exceptions
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st

from frontend.components.chat import render_chat_page
from frontend.components.sidebar import render_sidebar
from frontend.components.planning import render_planning_page
from frontend.components.literature import render_literature_page
from frontend.components.literature_review import render_literature_review_page
from frontend.components.manuscript import render_manuscript_page
from frontend.components.citations import render_citations_page
from frontend.components.reviewer import render_reviewer_page
from frontend.utils.session import get_state, get_storage, set_state, reset_workspace, save_current_project, slugify, inject_custom_css


st.set_page_config(
    page_title="ResearchForge",
    page_icon="📚",
    layout="wide",
)

# Inject modern custom stylesheet
inject_custom_css()


if "workspace_ready" not in st.session_state:
    st.session_state.workspace_ready = False
if "project_manager_mode" not in st.session_state:
    st.session_state.project_manager_mode = "manager"
if "agent_mode" not in st.session_state:
    st.session_state.agent_mode = "Smart Router (Recommended)"


state = get_state()

st.sidebar.markdown("<h2 class='gradient-title' style='font-size: 1.6rem;'>ResearchForge</h2>", unsafe_allow_html=True)
st.sidebar.caption("A LangGraph research workflow automation frontend")

if not st.session_state.workspace_ready:
    # Centered modern landing title
    st.markdown(
        """
        <div class="splash-container">
            <h1 class="gradient-title" style="font-size: 3.2rem;">ResearchForge</h1>
            <p style="color: #94a3b8; font-size: 1.15rem; margin-top: 0.5rem; margin-bottom: 0;">
                Deploy multi-agent swarms to plan, research, draft, and review academic manuscripts.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Create New Project", use_container_width=True, type="primary"):
            reset_workspace()
            st.session_state.project_manager_mode = "new"
            st.session_state.workspace_ready = False
            st.rerun()
    with col2:
        if st.button("📂 Open Existing Project", use_container_width=True):
            st.session_state.project_manager_mode = "open"
            st.rerun()

    # Form containers styled cleanly
    if st.session_state.project_manager_mode == "new":
        with st.container(border=True):
            st.markdown("### 🛠️ Configure New Project")
            st.caption("Provide topic details below to bootstrap the multi-agent workspace.")
            st.divider()
            
            project_name = st.text_input("Project Name (e.g. LLM Reasoning Survey)", key="new_project_name")
            project_topic = st.text_input("Topic / Core Research Question", key="new_project_topic")
            project_status = st.selectbox(
                "Initial Workspace Status",
                ["planning", "researching", "drafting", "reviewing"],
                key="new_project_status",
            )
            
            # Keep Save As filename input synchronized dynamically
            default_file_name = slugify(project_name or "untitled")
            if "new_project_file_name" not in st.session_state or st.session_state.get("_last_project_name") != project_name:
                st.session_state.new_project_file_name = default_file_name
                st.session_state._last_project_name = project_name
                
            project_file_name = st.text_input(
                "Save As (Filename)",
                key="new_project_file_name",
            )

            can_create = bool(project_name.strip() and project_topic.strip())
            st.divider()
            if st.button("🚀 Initialize Project Workspace", disabled=not can_create, type="primary", use_container_width=True):
                if project_name.strip() and project_topic.strip():
                    state.project_name = project_name.strip()
                    state.topic = project_topic.strip()
                    state.status = project_status
                    set_state(state)
                    save_current_project(state, project_file_name.strip() or project_name.strip())
                    st.session_state.workspace_ready = True
                    st.session_state.project_manager_mode = "workspace"
                    st.success("Project created and opened successfully!")
                    st.rerun()

    if st.session_state.project_manager_mode == "open":
        with st.container(border=True):
            st.markdown("### 📂 Open Saved Project")
            st.caption("Select a saved project from the list below.")
            st.divider()
            
            storage = get_storage()
            projects = storage.list_projects()
            if projects:
                selected = st.selectbox("Select Project Directory", projects)
                st.divider()
                if st.button("🔓 Open Selected Project Workspace", type="primary", use_container_width=True):
                    loaded_state = storage.load(selected)
                    set_state(loaded_state)
                    st.session_state.workspace_ready = True
                    st.session_state.project_manager_mode = "workspace"
                    st.success(f"Successfully loaded: {selected}")
                    st.rerun()
            else:
                st.info("No saved projects found yet. Click 'Create New Project' to start.")

    st.stop()

render_sidebar()

st.markdown("<h1 class='gradient-title'>ResearchForge</h1>", unsafe_allow_html=True)
st.caption("Plan, explore papers, synthesize literature, draft manuscripts, collect citations, and respond to reviewer feedback.")

with st.container():
    tab_chat, tab_planning, tab_literature, tab_review, tab_manuscript, tab_citations, tab_reviewer = st.tabs(
        ["Chat", "Planning", "Literature", "Literature Review", "Manuscript", "Citations", "Reviewer"]
    )

with tab_chat:
    render_chat_page()

with tab_planning:
    render_planning_page()

with tab_literature:
    render_literature_page()

with tab_review:
    render_literature_review_page()

with tab_manuscript:
    render_manuscript_page()

with tab_citations:
    render_citations_page()

with tab_reviewer:
    render_reviewer_page()
