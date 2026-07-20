from llm.ollama_provider import ollama_provider

from utils.parser import parse_json

from models.router_action import RouterAction

from config.prompts import ROUTER_SYSTEM_PROMPT


class WorkflowRouter:


    def __init__(self):

        self.llm = ollama_provider.get_llm()


    def route(
        self,
        user_input: str
    ) -> RouterAction:

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

        return RouterAction(
            **data
        )