from abc import ABC, abstractmethod

from llm import ollama_provider
from memory.state import ProjectState

from models.chat_message import ChatMessage
from models.workflow_event import WorkflowEvent

from utils.logger import logger
from utils.parser import parse_json


class BaseAgent(ABC):

    def __init__(self, name: str):

        self.name = name

        self.llm = ollama_provider.get_llm()

        self.logger = logger

    def _format_state(
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
        Project Name:
        {state.project_name}

        Topic:
        {state.topic}

        Description:
        {state.description}

        Objectives:
        {objectives}

        Keywords:
        {keywords}

        Current Status:
        {state.status}

        Current Agent:
        {state.current_agent}
        """

    @abstractmethod
    def _build_prompt(
        self,
        state: ProjectState,
        user_input: str
    ) -> str:

        pass


    @abstractmethod
    def _update_state(
        self,
        state: ProjectState,
        data: dict
    ) -> ProjectState:

        state.current_agent = self.name

        state.status = "citation"

        state.citations.extend(
            data["citations"]
        )

        return state


    def _invoke_llm(
            self,
            prompt: str,
            max_retries: int = 3
        ) -> dict:

            current_prompt = prompt

            last_error = None

            for attempt in range(max_retries):

                try:

                    response = self.llm.invoke(
                        current_prompt
                    )

                    return parse_json(
                        response.content
                    )
                    

                except Exception as e:

                    last_error = e

                    self.logger.warning(
                        f"{self.name} | Attempt {attempt + 1} failed."
                    )

                    current_prompt += """

                    Your previous response was not valid JSON.

                    Return ONLY a valid JSON object.

                    Do not include explanations.

                    Do not use Markdown.

                    Return JSON only.
                    """

            raise RuntimeError(
                f"{self.name} failed after {max_retries} attempts."
            ) from last_error


    def run(
            self,
            state: ProjectState,
            user_input: str
        ):

            self.logger.info(
                f"{self.name} started. User Input: {user_input}"
            )

            prompt = self._build_prompt(
                state,
                user_input
            )

            data = self._invoke_llm(
                prompt
            )

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
                    content=data["response"]
                )
            )

            state.conversation_outputs.append(
                {
                    "agent": self.name,
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