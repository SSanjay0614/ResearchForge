from agents.base_agent import BaseAgent

from memory.state import ProjectState

from models.reviewer_action import ReviewerAction

from config.prompts import (
    REVIEWER_SYSTEM_PROMPT,
    REVIEWER_ACTION_PROMPT
)

from examples.reviewer_examples import (
    REVIEWER_RESPONSE_PATTERNS
)

from utils.parser import parse_json


class ReviewerAgent(BaseAgent):


    def __init__(self):

        super().__init__(
            "Reviewer Agent"
        )


    def _build_prompt(
        self,
        state: ProjectState,
        user_input: str,
        strategy: str
    ) -> str:

        project = self._format_state(
            state
        )

        manuscript = f"""

Title

{state.manuscript.title}

Abstract

{state.manuscript.abstract}

Introduction

{state.manuscript.introduction}

Methodology

{state.manuscript.methodology}

Experiments

{state.manuscript.experiments}

Results

{state.manuscript.results}

Conclusion

{state.manuscript.conclusion}

"""

        pattern = REVIEWER_RESPONSE_PATTERNS[
            strategy
        ]

        return f"""
{REVIEWER_SYSTEM_PROMPT}

Project Information

{project}

Current Manuscript

{manuscript}

Reviewer Response Strategy

{strategy}

Response Pattern

{pattern}

Reviewer Comment

{user_input}
"""

    def _build_review_prompt(
        self,
        state: ProjectState,
        user_input: str,
        strategy: str
    ) -> str:

        project = self._format_state(
            state
        )

        manuscript = f"""

    Title

    {state.manuscript.title}

    Abstract

    {state.manuscript.abstract}

    Introduction

    {state.manuscript.introduction}

    Methodology

    {state.manuscript.methodology}

    Experiments

    {state.manuscript.experiments}

    Results

    {state.manuscript.results}

    Conclusion

    {state.manuscript.conclusion}

    """

        literature = f"""

    Literature Review

    {state.literature_review}

    Research Gap

    {state.research_gap}

    """

        pattern = REVIEWER_RESPONSE_PATTERNS[
            strategy
        ]

        return f"""
    {REVIEWER_SYSTEM_PROMPT}

    Project Information

    {project}

    Current Manuscript

    {manuscript}

    Literature Context

    {literature}

    Reviewer Response Strategy

    {strategy}

    Response Pattern

    {pattern}

    Reviewer Comment

    {user_input}

    Instructions

    Generate a professional response to the reviewer.

    Maintain a respectful and appreciative tone.

    If the reviewer requests additional experiments that are unavailable, never fabricate results.

    If manuscript revisions are required, clearly specify the suggested revision separately.

    Return ONLY JSON in the following format:

    {{
        "response": "",
        "manuscript_revision": ""
    }}
    """

    def _decide_strategy(
        self,
        reviewer_comment: str
    ) -> ReviewerAction:

        prompt = f"""
{REVIEWER_ACTION_PROMPT}

Reviewer Comment

{reviewer_comment}
"""

        response = self.llm.invoke(
            prompt
        )

        data = parse_json(
            response.content
        )

        return ReviewerAction(
            **data
        )


    def _update_state(
        self,
        state: ProjectState,
        data: dict
    ) -> ProjectState:

        state.current_agent = self.name

        state.status = "review"

        state.reviewer_response = {
            "response": data.get("response", ""),
            "manuscript_revision": data.get("manuscript_revision", ""),
        }

        return state


    def run(
        self,
        state: ProjectState,
        user_input: str
    ):

        action = self._decide_strategy(
            user_input
        )

        prompt = self._build_review_prompt(
            state,
            user_input,
            action.strategy
        )

        data = self._invoke_llm(
            prompt
        )

        state = self._update_state(
            state,
            data
        )

        return state, data