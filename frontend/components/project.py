import os
import sys

import streamlit as st

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from frontend.utils.session import get_state, get_storage, set_state, slugify, reset_workspace


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
