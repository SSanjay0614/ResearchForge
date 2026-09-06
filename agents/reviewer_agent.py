from agents.base_agent import BaseAgent

from memory.state import ProjectState

from models.reviewer_action import ReviewerAction
from models.chat_message import ChatMessage
from models.workflow_event import WorkflowEvent

from config.prompts import (
    REVIEWER_SYSTEM_PROMPT,
    REVIEWER_ACTION_PROMPT,
    REVIEWER_CRITIQUE_PROMPT,
    REVIEWER_REVISION_PROMPT,
    REVIEWER_RESPONSE_PATTERNS,
)

from utils.parser import parse_json

MAX_REVIEW_ITERATIONS = 2


class ReviewerAgent(BaseAgent):


    def __init__(self):

        super().__init__(
            "Reviewer Agent"
        )

    def _build_context(
        self,
        state: ProjectState,
        reviewer_comment: str
    ) -> str:

        manuscript = state.manuscript
        sections = []
        if manuscript.title:
            sections.append(f"Title: {manuscript.title}")
        if manuscript.abstract:
            sections.append(f"Abstract: {manuscript.abstract}")
        if manuscript.introduction:
            sections.append(f"Introduction: {manuscript.introduction}")
        if manuscript.methodology:
            sections.append(f"Methodology: {manuscript.methodology}")
        if manuscript.experiments:
            sections.append(f"Experiments: {manuscript.experiments}")
        if manuscript.results:
            sections.append(f"Results: {manuscript.results}")
        if manuscript.conclusion:
            sections.append(f"Conclusion: {manuscript.conclusion}")

        manuscript_text = "\n\n".join(sections) if sections else "None"

        return f"""
        Reviewer Comment:
        {reviewer_comment}

        Relevant Manuscript Sections:
        {manuscript_text}

        Literature Context:
        Literature Review: {state.literature_review or 'None'}
        Research Gap: {state.research_gap or 'None'}
        """

    def _build_prompt(
        self,
        state: ProjectState,
        user_input: str,
        strategy: str = "writing_revision"
    ) -> str:

        return self._build_review_prompt(
            state,
            user_input,
            strategy
        )

    def _build_review_prompt(
        self,
        state: ProjectState,
        user_input: str,
        strategy: str
    ) -> str:

        context = self._build_context(
            state,
            user_input
        )

        pattern = REVIEWER_RESPONSE_PATTERNS.get(
            strategy,
            ""
        )

        return f"""
    {REVIEWER_SYSTEM_PROMPT}

    Reviewer Context:
    {context}

    Reviewer Response Strategy:
    {strategy}

    Response Pattern:
    {pattern}

    Reviewer Comment:
    {user_input}

    Instructions:

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

    def _critique_response(
        self,
        state: ProjectState,
        reviewer_comment: str,
        draft_response: dict
    ) -> dict:

        context = self._build_context(state, reviewer_comment)

        prompt = f"""
        {REVIEWER_CRITIQUE_PROMPT}

        Context:
        {context}

        Draft Reviewer Response:
        {draft_response.get("response", "")}

        Suggested Manuscript Revision:
        {draft_response.get("manuscript_revision", "")}
        """

        try:
            return self._invoke_llm(prompt)
        except Exception:
            return {"acceptable": True, "critique": "", "revision_instructions": ""}

    def _build_revision_prompt(
        self,
        state: ProjectState,
        user_input: str,
        strategy: str,
        draft_response: dict,
        critique_info: dict
    ) -> str:

        context = self._build_context(state, user_input)

        pattern = REVIEWER_RESPONSE_PATTERNS.get(strategy, "")

        return REVIEWER_REVISION_PROMPT.format(
            system_prompt=REVIEWER_SYSTEM_PROMPT,
            context=context,
            strategy=strategy,
            pattern=pattern,
            draft_response=draft_response.get("response", ""),
            draft_revision=draft_response.get("manuscript_revision", ""),
            critique=critique_info.get("critique", ""),
            revision_instructions=critique_info.get("revision_instructions", "")
        )

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
            "reviewer_comment": data.get("reviewer_comment", ""),
            "response": data.get("response", ""),
            "manuscript_revision": data.get("manuscript_revision", ""),
        }

        return state

    def run(
        self,
        state: ProjectState,
        user_input: str
    ):

        self.logger.info(
            f"{self.name} started. User Input: {user_input}"
        )

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

        data["reviewer_comment"] = user_input

        critique_info = self._critique_response(
            state,
            user_input,
            data
        )

        if not critique_info.get("acceptable", True):

            self.logger.info("review response did not fully address concern")

            revision_prompt = self._build_revision_prompt(
                state,
                user_input,
                action.strategy,
                data,
                critique_info
            )

            try:
                revised_data = self._invoke_llm(revision_prompt)
                if revised_data.get("response"):
                    revised_data["reviewer_comment"] = user_input
                    data = revised_data
            except Exception as e:
                self.logger.warning(f"Reviewer revision pass failed: {e}")

        state = self._update_state(
            state,
            data
        )

        data["agent"] = self.name
        state.last_response = data

        state.chat_history.append(
            ChatMessage(
                role="user",
                content=user_input
            )
        )

        state.chat_history.append(
            ChatMessage(
                role="assistant",
                agent=self.name,
                content=data.get("response", "")
            )
        )

        state.conversation_outputs.append(
            {
                "agent": self.name,
                "reviewer_comment": user_input,
                "response": data.get("response", ""),
                "questions": data.get("questions", []),
                "papers": data.get("papers", []),
                "citations": data.get("citations", []),
                "manuscript_revision": data.get("manuscript_revision", ""),
            }
        )

        state.workflow_history.append(
            WorkflowEvent(
                agent=self.name,
                action="Completed"
            )
        )

        self.logger.info(
            f"{self.name} finished."
        )

        return state, data