from agents.base_agent import BaseAgent

from memory.state import ProjectState

from models.citation import Citation
from models.citation_action import CitationAction

from config.prompts import (
    CITATION_ACTION_PROMPT
)

from llm.ollama_provider import ollama_provider

from utils.parser import parse_json

from tools.crossref_tool import CrossrefTool
from tools.openalex_tool import OpenAlexTool


class CitationAgent(BaseAgent):


    def __init__(self):

        super().__init__(
            "Citation Agent"
        )

        self.llm = ollama_provider.get_llm()

        self.crossref = CrossrefTool()

        self.openalex = OpenAlexTool()


    def _build_prompt(
        self,
        state: ProjectState,
        user_input: str
    ) -> str:

        return ""
    
    def _decide_workflow(
        self,
        user_input: str
    ) -> CitationAction:

        prompt = f"""
{CITATION_ACTION_PROMPT}

User Request

{user_input}
"""

        response = self.llm.invoke(
            prompt
        )

        data = parse_json(
            response.content
        )

        return CitationAction(
            **data
        )


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


    def run(
        self,
        state: ProjectState,
        user_input: str
    ):

        action = self._decide_workflow(
            user_input
        )

        citations = []

        # -------------------------------------------------
        # Project Papers
        # -------------------------------------------------

        if action.workflow == "project":

            for paper in state.papers:

                doi = paper.metadata.doi

                if doi.startswith(
                    "https://doi.org/"
                ):

                    doi = doi.replace(
                        "https://doi.org/",
                        ""
                    )

                if not doi:

                    continue

                try:

                    bibtex = self.crossref.get_bibtex(
                        doi
                    )

                    citations.append(

                        Citation(

                            title=paper.metadata.title,

                            authors=", ".join(
                                paper.metadata.authors
                            ),

                            year=paper.metadata.year,

                            doi=doi,

                            bibtex=bibtex

                        )

                    )

                except Exception:

                    continue

        # -------------------------------------------------
        # Paper Title
        # -------------------------------------------------

        elif action.workflow == "title":

            paper = self.openalex.search_title(
                action.title
            )

            if paper:

                try:

                    bibtex = self.crossref.get_bibtex(
                        paper.doi
                    )

                    citations.append(

                        Citation(

                            title=paper.title,

                            authors=paper.authors,

                            year=paper.year,

                            doi=paper.doi,

                            bibtex=bibtex

                        )

                    )

                except Exception:

                    pass

        # -------------------------------------------------
        # Research Claim
        # -------------------------------------------------

        elif action.workflow == "claim":

            papers = self.openalex.run(
                action.query,
                max_results=5
            )

            for paper in papers:

                doi = paper.metadata.doi

                if doi.startswith(
                    "https://doi.org/"
                ):

                    doi = doi.replace(
                        "https://doi.org/",
                        ""
                    )

                if not doi:

                    continue

                try:

                    bibtex = self.crossref.get_bibtex(
                        doi
                    )

                    citations.append(

                        Citation(

                            title=paper.metadata.title,

                            authors=", ".join(
                                paper.metadata.authors
                            ),

                            year=paper.metadata.year,

                            doi=doi,

                            bibtex=bibtex

                        )

                    )

                except Exception:

                    continue

        data = {

            "response": f"Generated {len(citations)} citation(s).",

            "citations": citations,

            "count": len(citations)

        }

        state = self._update_state(
            state,
            data
        )

        return state, data