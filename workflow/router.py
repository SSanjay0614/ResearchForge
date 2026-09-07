import re

from llm.ollama_provider import ollama_provider

from utils.parser import parse_json

from models.router_action import RouterAction

from config.prompts import ROUTER_SYSTEM_PROMPT


# Agent -> the agent that produces what it needs. Used to redirect when the
# LLM names an unmet precondition but still routes at the blocked agent.
PRECONDITION_FALLBACK = {
    "synthesis": "literature",
    "manuscript": "synthesis",
    "reviewer": "manuscript"
}


# A request that reports reviewer feedback belongs to the reviewer agent even
# when it reads as a complaint about the manuscript ("the reviewer states that
# the manuscript lacks deployment metrics"). The LLM hears the manuscript half
# of that and routes to the manuscript agent, which then edits text instead of
# drafting a response. The wording is formulaic enough to settle in code, so it
# is settled here rather than left to the prompt alone.

REVIEWER_CUES = re.compile(
    r"""
    \b(
        reviewer[s]?\b
        | referee[s]?\b
        | rebuttal
        | \bR[123]\b
        | response\s+to\s+review
        | review(er)?\s+comment
    )
    """,
    re.IGNORECASE | re.VERBOSE
)

# Phrases that mean "do this to the manuscript", which outrank a passing
# mention of a reviewer: "rewrite the intro to address the reviewer" is an
# editing instruction, not a request for a rebuttal.
DIRECT_EDIT_CUES = re.compile(
    r"""
    \b(
        write | rewrite | draft | expand | shorten | polish
        | generate | continue | edit | revise\s+the\s+(text|wording|section)
    )\b
    """,
    re.IGNORECASE | re.VERBOSE
)


class WorkflowRouter:

    # The chat UI routes once to label the spinner and decide the
    # pre-manuscript checkpoint, then the graph routes again to pick the node.
    # Both see the same user input and the same state, so the second call is
    # served from here instead of costing another LLM round trip. Shared across
    # instances because graph.py and chat.py each build their own router.

    _cache = {}

    _CACHE_LIMIT = 8

    def __init__(self):

        self.llm = ollama_provider.get_llm()

    def _state_signature(
        self,
        state
    ) -> str:
        """Compact description of what the project already holds.

        Kept short deliberately: it goes into every routing prompt, and a
        handful of counts is enough to tell which agents can actually run.
        """

        if state is None:

            return "No project state available."

        papers = getattr(state, "papers", []) or []

        relevant = sum(
            1
            for paper in papers
            if getattr(paper, "is_relevant", True)
        )

        manuscript = getattr(state, "manuscript", None)

        section_count = 0

        if manuscript is not None:

            for field in [
                "title",
                "abstract",
                "introduction",
                "literature_review",
                "methodology",
                "experiments",
                "results",
                "discussion",
                "conclusion"
            ]:

                if (getattr(manuscript, field, "") or "").strip():

                    section_count += 1

            section_count += sum(
                1
                for content in (getattr(manuscript, "sections", {}) or {}).values()
                if (content or "").strip()
            )

        pre_info = getattr(state, "pre_manuscript_info", None) or {}

        filled_pre_info = sum(
            1
            for value in pre_info.values()
            if (value or "").strip()
        )

        return "\n".join([
            "- topic: %s" % (
                "set"
                if (getattr(state, "topic", "") or "").strip()
                else "none"
            ),
            "- objectives: %d" % len(getattr(state, "objectives", []) or []),
            "- papers collected: %d (%d relevant)" % (len(papers), relevant),
            "- literature review: %s" % (
                "present"
                if (getattr(state, "literature_review", "") or "").strip()
                else "none"
            ),
            "- research gap: %s" % (
                "present"
                if (getattr(state, "research_gap", "") or "").strip()
                else "none"
            ),
            "- pre-manuscript information: %d field(s) filled" % filled_pre_info,
            "- manuscript sections written: %d" % section_count,
            "- citations: %d" % len(getattr(state, "citations", []) or []),
            "- reviewer comments: %d" % len(
                getattr(state, "reviewer_comments", []) or []
            ),
            "- last agent: %s" % (getattr(state, "current_agent", "") or "none")
        ])

    def _cache_key(
        self,
        user_input: str,
        signature: str
    ):
        """Cache on the input *and* the state.

        Keying on the input alone would make "continue" return whatever it
        resolved to the first time, long after the project moved on.
        """

        return (
            (user_input or "").strip(),
            signature
        )

    def _looks_like_reviewer_comment(
        self,
        user_input: str
    ) -> bool:
        """Whether the request is reporting reviewer feedback."""

        text = (user_input or "").strip()

        if not text:

            return False

        if not REVIEWER_CUES.search(text):

            return False

        # A direct instruction to write or rewrite wins, even with a reviewer
        # mentioned as the motivation.
        return not DIRECT_EDIT_CUES.search(text)

    def _correct_reviewer_route(
        self,
        action: RouterAction,
        user_input: str
    ) -> RouterAction:
        """Send reviewer feedback to the reviewer agent.

        Only overrides the manuscript agent. The others are not confusable with
        a reviewer comment, and overriding a deliberate literature or citation
        route on a keyword would be worse than the bug being fixed.
        """

        if action.agent != "manuscript":

            return action

        if not self._looks_like_reviewer_comment(user_input):

            return action

        action.requested_agent = action.agent

        action.agent = "reviewer"

        action.reason = (
            "The request reports reviewer feedback, so it needs a reviewer "
            "response rather than a direct manuscript edit."
        )

        return action

    def _resolve_block(
        self,
        action: RouterAction
    ) -> RouterAction:
        """Honour a named precondition even if the LLM still routed past it."""

        if not (action.blocked_by or "").strip():

            return action

        # A reviewer comment carries its own subject matter, so "no reviewer
        # comments recorded" is never a reason to redirect: the comment is the
        # request. Redirecting here sent rebuttal requests to the manuscript
        # agent, which is the bug this guards.
        if action.agent == "reviewer" and "reviewer comment" in (
            action.blocked_by or ""
        ).lower():

            action.blocked_by = ""

            return action

        fallback = PRECONDITION_FALLBACK.get(
            action.agent
        )

        if fallback:

            action.requested_agent = action.agent

            action.agent = fallback

        return action

    def route(
        self,
        user_input: str,
        state=None
    ) -> RouterAction:

        signature = self._state_signature(
            state
        )

        key = self._cache_key(
            user_input,
            signature
        )

        if key[0] and key in WorkflowRouter._cache:

            return WorkflowRouter._cache[key]

        prompt = f"""
{ROUTER_SYSTEM_PROMPT}

Project State

{signature}

User Request

{user_input}
"""

        response = self.llm.invoke(
            prompt
        )

        data = parse_json(
            response.content
        )

        action = RouterAction(
            **data
        )

        # Correct the reviewer/manuscript confusion before the precondition
        # check, so a redirect is decided against the agent that should
        # actually run.
        action = self._correct_reviewer_route(
            action,
            user_input
        )

        action = self._resolve_block(
            action
        )

        if key[0]:

            if len(WorkflowRouter._cache) >= WorkflowRouter._CACHE_LIMIT:

                WorkflowRouter._cache.clear()

            WorkflowRouter._cache[key] = action

        return action
