from agents.base_agent import BaseAgent

from memory.state import ProjectState

from models.citation import Citation
from models.citation_action import CitationAction

from config.prompts import (
    CITATION_ACTION_PROMPT,
    CLAIM_SUPPORT_EVALUATION_PROMPT,
    QUERY_REFORMULATION_PROMPT,
)

from llm.ollama_provider import ollama_provider

from utils.parser import parse_json

from tools.crossref_tool import CrossrefTool
from tools.openalex_tool import OpenAlexTool

MAX_CLAIM_SEARCH_ITERATIONS = 3


class CitationAgent(BaseAgent):


    def __init__(self):

        super().__init__(
            "Citation Agent"
        )

        self.llm = ollama_provider.get_llm()

        self.crossref = CrossrefTool()

        self.openalex = OpenAlexTool()

    def _build_context(
        self,
        action: CitationAction,
        user_input: str
    ) -> str:

        if action.workflow == "title":
            return f"Requested Paper Title: {action.title}"
        elif action.workflow == "claim":
            return f"Research Claim: {user_input or action.query}"
        return "Project Papers Citation Request"

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

    def _evaluate_claim_support(
        self,
        paper,
        claim: str
    ) -> bool:

        title = getattr(paper.metadata, "title", "") if hasattr(paper, "metadata") else getattr(paper, "title", "")
        abstract = getattr(paper.metadata, "abstract", "") if hasattr(paper, "metadata") else getattr(paper, "abstract", "")

        if not title:
            return False

        prompt = f"""
        {CLAIM_SUPPORT_EVALUATION_PROMPT}

        Research Claim:
        {claim}

        Paper Title:
        {title}

        Paper Abstract:
        {abstract or 'N/A'}
        """

        try:
            data = self._invoke_llm(prompt)
            return data.get("supports_claim", True)
        except Exception:
            return True

    def _reformulate_claim_query(
        self,
        claim: str,
        current_query: str
    ) -> str:

        prompt = f"""
        {QUERY_REFORMULATION_PROMPT}

        Research Claim:
        {claim}

        Previous Query:
        {current_query}
        """

        try:
            data = self._invoke_llm(prompt)
            new_query = data.get("query", "").strip()
            return new_query if new_query else current_query
        except Exception:
            return f"{claim} evidence"

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

    def _citation_for_project_paper(self, paper) -> Citation:
        metadata = paper.metadata
        doi = (metadata.doi or "").strip()
        if doi.startswith("https://doi.org/"):
            doi = doi.replace("https://doi.org/", "", 1)
        elif doi.startswith("http://doi.org/"):
            doi = doi.replace("http://doi.org/", "", 1)

        authors = ", ".join(metadata.authors)
        venue = metadata.venue or ""
        year = metadata.year
        bibtex = None

        if doi:
            bibtex = self.crossref.get_bibtex(doi)
        elif metadata.title:
            matches = self.crossref.run(metadata.title, rows=1)
            if matches:
                match = matches[0]
                doi = match.doi or ""
                authors = match.authors or authors
                venue = match.venue or venue
                year = match.year or year
                bibtex = self.crossref.get_bibtex(doi) if doi else None

        return Citation(
            title=metadata.title,
            authors=authors,
            year=year,
            doi=doi,
            bibtex=bibtex or "",
            venue=venue,
        )

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
                try:
                    citations.append(self._citation_for_project_paper(paper))

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

            claim_text = user_input or action.query
            current_query = action.query or claim_text

            for iteration in range(1, MAX_CLAIM_SEARCH_ITERATIONS + 1):

                try:
                    candidate_papers = self.openalex.run(
                        current_query,
                        max_results=5
                    )
                except Exception:
                    candidate_papers = []

                supporting_papers = []
                for paper in candidate_papers:
                    if self._evaluate_claim_support(paper, claim_text):
                        supporting_papers.append(paper)

                if supporting_papers:
                    for paper in supporting_papers:

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

                if citations:
                    break

                if iteration < MAX_CLAIM_SEARCH_ITERATIONS:
                    self.logger.info("insufficient supporting papers for claim")
                    current_query = self._reformulate_claim_query(
                        claim_text,
                        current_query
                    )

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