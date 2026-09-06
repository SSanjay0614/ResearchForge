import re
import time

from langchain_core.messages import AIMessage
from langchain_ollama import ChatOllama

from config.settings import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    LLM_BACKEND,
    MAX_TOKENS,
    OLLAMA_API_KEY,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_NUM_CTX,
    TEMPERATURE
)


class GoogleLLM:
    """Gemini wrapped to match the small slice of the ChatOllama API we use."""

    def __init__(
        self,
        model: str = GEMINI_MODEL
    ):

        from google import genai

        if not GEMINI_API_KEY:

            raise RuntimeError(
                "LLM_BACKEND=gemini but GEMINI_API_KEY is not set."
            )

        self.model = model

        self.client = genai.Client(
            api_key=GEMINI_API_KEY
        )

    def invoke(
        self,
        prompt
    ) -> AIMessage:

        text = (
            prompt
            if isinstance(prompt, str)
            else str(prompt)
        )

        last_error = None

        # The free tier enforces a small per-day and per-minute request quota,
        # and concurrent relevance checks trip it easily. A 429 here would
        # otherwise surface as a paper with no analysis.

        for attempt in range(4):

            try:

                response = self.client.models.generate_content(

                    model=self.model,

                    contents=text,

                    config={
                        "temperature": TEMPERATURE,
                        "max_output_tokens": MAX_TOKENS
                    }
                )

                return AIMessage(
                    content=response.text or ""
                )

            except Exception as e:

                last_error = e

                if "RESOURCE_EXHAUSTED" not in str(e) and "429" not in str(e):

                    raise

                time.sleep(self._retry_delay(str(e), attempt))

        raise last_error

    def _retry_delay(
        self,
        message: str,
        attempt: int
    ) -> float:

        match = re.search(
            r"retry in ([0-9.]+)s",
            message
        )

        if match:

            return min(float(match.group(1)) + 0.5, 30.0)

        return min(2 ** attempt, 30.0)


class OllamaProvider:
    """Single entry point for the chat model, whichever backend is configured."""

    def __init__(self):

        self.backend = LLM_BACKEND

        if self.backend == "gemini":

            self.llm = GoogleLLM()

        else:

            # With a local daemon there is nothing to add: it signs cloud
            # requests itself with the key pair from `ollama signin`. When
            # OLLAMA_BASE_URL points straight at https://ollama.com there is no
            # daemon in the path, so the key has to travel as a bearer token.
            client_kwargs = {}

            if OLLAMA_API_KEY:

                client_kwargs["headers"] = {
                    "Authorization": "Bearer " + OLLAMA_API_KEY
                }

            self.llm = ChatOllama(
                model=OLLAMA_MODEL,
                base_url=OLLAMA_BASE_URL,
                temperature=TEMPERATURE,
                num_predict=MAX_TOKENS,
                num_ctx=OLLAMA_NUM_CTX,
                client_kwargs=client_kwargs
            )

    def get_llm(self):

        return self.llm

    def describe(self) -> str:

        return (
            "gemini:" + GEMINI_MODEL
            if self.backend == "gemini"
            else "ollama:" + OLLAMA_MODEL
        )


ollama_provider = OllamaProvider()
