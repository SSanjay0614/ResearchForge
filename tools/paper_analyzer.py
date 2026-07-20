import json

from tools.base_tool import BaseTool

from models.paper_analysis import PaperAnalysis

from llm.ollama_provider import ollama_provider

from config.prompts import PAPER_ANALYSIS_SYSTEM_PROMPT

from utils.parser import parse_json

class PaperAnalyzer(BaseTool):

    def __init__(self):

        super().__init__("Paper Analyzer")

        self.llm = ollama_provider.get_llm()

    def run(
        self,
        text: str
    ) -> PaperAnalysis:

        prompt = f"""
        {PAPER_ANALYSIS_SYSTEM_PROMPT}

        Paper:

        {text}
        """

        for attempt in range(2):

            
            response = self.llm.invoke(
                prompt
            )

            content = (
                response.content
                if hasattr(response, "content")
                else str(response)
            )
            

            try:

                data = parse_json(
                    content
                )

                return PaperAnalysis(
                    **data
                )

            except Exception:

                if attempt == 0:

                    prompt = f"""
    Your previous response was not valid JSON.

    Return ONLY valid JSON.

    Do not include markdown.

    Do not include explanations.

    {prompt}
    """

                else:

                    raise