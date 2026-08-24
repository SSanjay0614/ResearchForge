from agents.base_agent import BaseAgent

from memory.state import ProjectState

from config.prompts import PLANNING_SYSTEM_PROMPT


class PlanningAgent(BaseAgent):

    def __init__(self):

        super().__init__("Planning Agent")

    def _build_context(
        self,
        state: ProjectState
    ) -> str:

        objectives = "\n".join(
            f"- {obj}"
            for obj in state.objectives
        ) or "None"

        keywords = "\n".join(
            f"- {key}"
            for key in state.keywords
        ) or "None"

        return f"""
        Topic:
        {state.topic or "None"}

        Description:
        {state.description or "None"}

        Objectives:
        {objectives}

        Keywords:
        {keywords}

        Literature Review:
        {state.literature_review or "None"}

        Research Gap:
        {state.research_gap or "None"}
        """

    def _build_prompt(
        self,
        state: ProjectState,
        user_input: str
    ) -> str:

        return f"""
        {PLANNING_SYSTEM_PROMPT}

        Planning Context

        {self._build_context(state)}

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