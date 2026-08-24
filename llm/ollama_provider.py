from langchain_ollama import ChatOllama

from config.settings import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    TEMPERATURE
)


class OllamaProvider:

    def __init__(self):

        self.llm = ChatOllama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=TEMPERATURE,
            num_predict=4096
        )

    def get_llm(self):
        return self.llm


ollama_provider = OllamaProvider()


# from google import genai
# from langchain_core.messages import AIMessage

# from config.settings import (
#     GEMINI_API_KEY,
#     TEMPERATURE
# )


# class GoogleLLM:

#     def __init__(self):

#         self.client = genai.Client(
#             api_key=GEMINI_API_KEY
#         )

#     def invoke(self, prompt):

#         response = self.client.models.generate_content(
#             model="gemma-4-31b-it",
#             contents=prompt,
#             config={
#                 "temperature": TEMPERATURE,
#                 "max_output_tokens": 4096
#             }
#         )

#         return AIMessage(
#             content=response.text
#         )


# class OllamaProvider:

#     def __init__(self):

#         self.llm = GoogleLLM()

#     def get_llm(self):

#         return self.llm


# ollama_provider = OllamaProvider()