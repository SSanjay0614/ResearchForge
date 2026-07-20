from agents.base_agent import BaseAgent

from memory.state import ProjectState

from config.prompts import PLANNING_SYSTEM_PROMPT


class PlanningAgent(BaseAgent):

    def __init__(self):

        super().__init__("Planning Agent")


    def _build_prompt(
        self,
        state: ProjectState,
        user_input: str
    ) -> str:

        return f"""
        {PLANNING_SYSTEM_PROMPT}

        Current Project State

        {self._format_state(state)}

        User Request:
        {user_input}
        """


    def _update_state(
        self,
        state: ProjectState,
        data: dict
    ) -> ProjectState:

        state.current_agent = self.name
        
        state.needs_more_information = data.get(
            "needs_more_information",
            False
        )

        state.status = "planning"

        state.topic = data.get("topic", state.topic)

        state.description = data.get(
            "description",
            state.description
        )

        state.objectives = data.get(
            "objectives",
            state.objectives
        )

        state.keywords = data.get(
            "keywords",
            state.keywords
        )
        
        state.needs_more_information = data.get(
            "needs_more_information",
            False
        )

        return state