import os
import sys

import streamlit as st
from memory.state import ProjectState

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from frontend.utils.session import get_state, get_storage, set_state, slugify, reset_workspace, save_current_project, set_pending_checkpoint


PRE_MANUSCRIPT_FIELDS = [
    ("research_topic", "Research Topic / General Idea"),
    ("research_description", "Research Description / Problem"),
    ("objectives", "Objectives"),
    ("literature_review", "Literature Review / Related Work"),
    ("methodology", "Methodology / Approach"),
    ("dataset_setup", "Dataset / Experimental Setup"),
    ("results_findings", "Results / Findings"),
    ("ablation_studies", "Ablation Studies"),
    ("additional_notes", "Additional Information / Notes"),
    ("target_venue", "Target Venue / Format"),
]


def _pre_manuscript_defaults(state):
    existing = getattr(state, "pre_manuscript_info", None) or {}
    return {
        "research_topic": existing.get("research_topic") or state.topic,
        "research_description": existing.get("research_description") or state.description,
        "objectives": existing.get("objectives") or "\n".join(state.objectives),
        "literature_review": existing.get("literature_review") or state.literature_review,
        "methodology": existing.get("methodology") or "",
        "dataset_setup": existing.get("dataset_setup") or "",
        "results_findings": existing.get("results_findings") or "",
        "ablation_studies": existing.get("ablation_studies") or "",
        "additional_notes": existing.get("additional_notes") or state.research_gap,
        "target_venue": existing.get("target_venue") or "",
    }


def render_pre_manuscript_info(prefix: str = "sidebar", checkpoint: bool = False):
    state = get_state()
    if not all(
        hasattr(state, field_name)
        for field_name in ["pre_manuscript_info", "pre_manuscript_completed", "pending_checkpoint"]
    ):
        state_data = state.model_dump() if hasattr(state, "model_dump") else state.dict()
        state = ProjectState(**state_data)
        set_state(state)
    defaults = _pre_manuscript_defaults(state)
    if checkpoint:
        st.markdown("### Pre-Manuscript Info")
        st.info("Complete this information before Manuscript Agent runs. It will be used as manuscript context.")

    values = {}
    for field_key, label in PRE_MANUSCRIPT_FIELDS:
        value_key = f"{prefix}_pre_manuscript_{field_key}"
        if value_key not in st.session_state:
            st.session_state[value_key] = defaults[field_key]

        with st.expander(f"📝 {label}", expanded=field_key in {"research_topic", "research_description"}):
            values[field_key] = st.text_area(
                f"Edit {label}",
                height=180,
                key=value_key,
                label_visibility="collapsed",
            )

    button_label = "Save & Continue to Manuscript" if checkpoint else "Save Pre-Manuscript Info"
    submitted = st.button(button_label, key=f"{prefix}_pre_manuscript_save", type="primary", use_container_width=True)
    if not submitted:
        return False

    pre_manuscript_info = {key: value.strip() for key, value in values.items()}
    object.__setattr__(state, "pre_manuscript_info", pre_manuscript_info)
    state.topic = pre_manuscript_info["research_topic"] or state.topic
    state.description = pre_manuscript_info["research_description"] or state.description
    state.objectives = [line.strip() for line in pre_manuscript_info["objectives"].splitlines() if line.strip()]
    if checkpoint:
        object.__setattr__(state, "pre_manuscript_completed", True)
        state = set_pending_checkpoint(state, {})
    set_state(state)
    save_current_project(state)
    return True


def render_project_actions() -> None:
    state = get_state()
    storage = get_storage()

    st.sidebar.markdown("### 📋 Project Settings")
    
    # Synchronize sidebar values with the current state object (e.g. if updated by backend or loaded)
    sync_fields = [
        ("sidebar_current_project_name", state.project_name or "Not set"),
        ("sidebar_topic", state.topic or ""),
        ("sidebar_status", state.status or "planning"),
        ("sidebar_agent", state.current_agent or "Waiting"),
    ]
    for key, val in sync_fields:
        if key not in st.session_state or st.session_state[key] != val:
            st.session_state[key] = val

    st.sidebar.text_input("Project Name", key="sidebar_current_project_name")
    st.sidebar.text_input("Topic", key="sidebar_topic")
    st.sidebar.text_input("Status", key="sidebar_status")
    st.sidebar.text_input("Current Agent", key="sidebar_agent")

    # Update state from sidebar inputs immediately if user edits them
    state.project_name = st.session_state.sidebar_current_project_name
    state.topic = st.session_state.sidebar_topic
    state.status = st.session_state.sidebar_status
    state.current_agent = st.session_state.sidebar_agent

    st.sidebar.divider()
    st.sidebar.subheader("Actions")

    if st.sidebar.button("➕ New Project Workspace", use_container_width=True):
        reset_workspace()
        st.session_state.project_manager_mode = "new"
        st.rerun()

    project_names = storage.list_projects()
    selected_project = st.sidebar.selectbox(
        "Open Saved Project",
        options=["-- select --", *project_names],
        index=0,
        key="sidebar_open_project_select",
    )

    if st.sidebar.button("📂 Load Selected", use_container_width=True):
        if selected_project and selected_project != "-- select --":
            loaded_state = storage.load(selected_project)
            set_state(loaded_state)
            st.session_state.workspace_ready = True
            st.session_state.project_manager_mode = "workspace"
            st.sidebar.success(f"Loaded project: {selected_project}")
            st.rerun()

    # Sync Save As filename
    default_save_filename = slugify(state.project_name or "untitled")
    if "save_filename" not in st.session_state or st.session_state.get("_last_save_filename_project_name") != state.project_name:
        st.session_state["save_filename"] = default_save_filename
        st.session_state["_last_save_filename_project_name"] = state.project_name

    project_file_name = st.sidebar.text_input(
        "Save As (Filename)",
        key="save_filename",
    )

    if st.sidebar.button("💾 Save Project State", use_container_width=True, type="primary"):
        state.project_name = state.project_name or project_file_name or "untitled"
        storage.save(state, project_file_name or slugify(state.project_name))
        st.sidebar.success(f"Saved to disk!")
        st.rerun()

    delete_candidate = st.sidebar.selectbox(
        "Delete Saved Project",
        options=["-- select --", *project_names],
        key="delete_project_select",
    )

    if st.sidebar.button("🗑️ Delete Selected", use_container_width=True):
        if delete_candidate and delete_candidate != "-- select --":
            storage.delete(delete_candidate)
            st.sidebar.success(f"Deleted project: {delete_candidate}")
            st.rerun()

def render_project_info() -> None:
    render_project_actions()
