from llm.ollama_provider import ollama_provider

from utils.parser import parse_json

from models.router_action import RouterAction

from config.prompts import ROUTER_SYSTEM_PROMPT


class WorkflowRouter:

    # The chat UI routes once to label the spinner and decide the
    # pre-manuscript checkpoint, then the graph routes again to pick the node.
    # Both see the same user input, so the second call is served from here
    # instead of costing another LLM round trip. Shared across instances
    # because graph.py and chat.py each build their own router.

    _cache = {}

    _CACHE_LIMIT = 8

    def __init__(self):

        self.llm = ollama_provider.get_llm()


    def route(
        self,
        user_input: str
    ) -> RouterAction:

        key = (user_input or "").strip()

        if key and key in WorkflowRouter._cache:

            return WorkflowRouter._cache[key]

        prompt = f"""
{ROUTER_SYSTEM_PROMPT}

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

        if key:

            if len(WorkflowRouter._cache) >= WorkflowRouter._CACHE_LIMIT:

                WorkflowRouter._cache.clear()

            WorkflowRouter._cache[key] = action

        return action
