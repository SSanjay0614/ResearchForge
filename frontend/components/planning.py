import os
import sys

import streamlit as st

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from frontend.utils.session import get_state


def render_planning_page() -> None:
    state = get_state()

    planning_outputs = [
        output for output in (state.conversation_outputs or [])
        if output.get("agent") == "Planning Agent"
    ]

    st.subheader("Planning History")
    if planning_outputs:
        for index, data in enumerate(planning_outputs, start=1):
            response = data.get("response", "")
            if response:
                st.markdown(f"### Plan #{index}")
                st.info(response)
                st.divider()
    else:
        st.info("No planning output available yet.")
