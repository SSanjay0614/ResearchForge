from pydantic import BaseModel


class RouterAction(BaseModel):

    agent: str = ""

    # Why this agent was picked. Shown in the UI so a surprising route is
    # explainable instead of just wrong-looking.
    reason: str = ""

    # Set when the agent the user asked for could not run yet because the
    # project is missing something it needs (synthesis without papers, a
    # review without a manuscript). Holds the unmet precondition, and `agent`
    # is redirected to whichever agent produces it.
    blocked_by: str = ""

    # The agent the request originally pointed at, kept when a precondition
    # redirect changes `agent`.
    requested_agent: str = ""
