from agents.base_agent import BaseAgent

from memory.state import ProjectState

from models.citation import Citation
from models.citation_action import CitationAction

from models.citation_verification import CitationVerification

from config.prompts import (
    CITATION_ACTION_PROMPT,
    CLAIM_SUPPORT_EVALUATION_PROMPT,
    QUERY_REFORMULATION_PROMPT,
)

from config.settings import CITATION_REPAIR_MATCH_THRESHOLD

from llm.ollama_provider import ollama_provider

from utils.parser import parse_json

from tools.crossref_tool import CrossrefTool
from tools.openalex_tool import OpenAlexTool
from tools.citation_verifier import CitationVerifier

MAX_CLAIM_SEARCH_ITERATIONS = 3


class CitationAgent(BaseAgent):


    def __init__(self):

        super().__init__(
            "Citation Agent"
        )

        self.llm = ollama_provider.get_llm()

        self.crossref = CrossrefTool()

        self.openalex = OpenAlexTool()

        self.verifier = CitationVerifier()

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

    def _paper_evidence(
        self,
        paper
    ) -> str:
        """The strongest text we hold about a paper, for judging claim support.

        Prefers the stored analysis, which for arXiv papers is derived from the
        full text, and falls back to the abstract.
        """

        analysis = getattr(paper, "analysis", None)

        if analysis is not None:

            parts = []

            for label, field in [
                ("Problem", "problem_statement"),
                ("Contribution", "contribution"),
                ("Methodology", "methodology"),
                ("Datasets", "datasets"),
                ("Metrics", "metrics"),
                ("Results", "results"),
                ("Limitations", "limitations")
            ]:

                value = getattr(analysis, field, "")

                if isinstance(value, list):

                    value = ", ".join(str(item) for item in value)

                if (value or "").strip():

                    parts.append("%s: %s" % (label, value))

            if parts:

                return "\n".join(parts)

        if hasattr(paper, "metadata"):

            return getattr(paper.metadata, "abstract", "") or ""

        return getattr(paper, "abstract", "") or ""

    def _evaluate_claim_support(
        self,
        paper,
        claim: str
    ) -> dict:
        """Judge whether a paper supports a claim.

        Returns the verdict rather than a bare bool, because "could not tell"
        has to stay distinct from "yes". Defaulting to support is what lets an
        unchecked paper be cited as though it had been checked.
        """

        title = getattr(paper.metadata, "title", "") if hasattr(paper, "metadata") else getattr(paper, "title", "")

        if not title:

            return {
                "supports_claim": False,
                "confidence": "low",
                "reason": "Paper has no title to check."
            }

        evidence = self._paper_evidence(paper)

        if not evidence.strip():

            return {
                "supports_claim": False,
                "confidence": "low",
                "reason": "No abstract or analysis available to judge the claim against."
            }

        prompt = f"""
        {CLAIM_SUPPORT_EVALUATION_PROMPT}

        Research Claim:
        {claim}

        Paper Title:
        {title}

        Paper Evidence:
        {evidence}
        """

        try:

            data = self._invoke_llm(prompt)

            return {
                "supports_claim": bool(data.get("supports_claim", False)),
                "confidence": data.get("confidence", "low"),
                "reason": data.get("reason", "")
            }

        except Exception as e:

            self.logger.warning(
                f"claim support check failed: {e}"
            )

            return {
                "supports_claim": False,
                "confidence": "low",
                "reason": "Claim support could not be checked (%s)." % type(e).__name__
            }

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

    def _best_title_match(
        self,
        title: str,
        year: int = 0
    ):
        """The Crossref hit that is actually the paper we asked for, or None.

        Crossref always answers, so a query for a paper it does not index
        returns the nearest unrelated work. Taking that on trust is what put a
        social-care book chapter behind a deep-learning citation.
        """

        title = (title or "").strip()

        if not title:

            return None

        try:

            matches = self.crossref.run(title, rows=5)

        except Exception as e:

            self.logger.info(
                "Crossref title search failed for %r: %s"
                % (title[:60], type(e).__name__)
            )

            return None

        best = None

        best_similarity = 0.0

        for match in matches or []:

            similarity = self.verifier.title_similarity(
                title,
                getattr(match, "title", "") or ""
            )

            if similarity > best_similarity:

                best = match

                best_similarity = similarity

        if best is None or best_similarity < CITATION_REPAIR_MATCH_THRESHOLD:

            if best is not None:

                self.logger.info(
                    "rejected Crossref match for %r: closest was %r (%.2f)"
                    % (
                        title[:60],
                        (getattr(best, "title", "") or "")[:60],
                        best_similarity
                    )
                )

            return None

        match_year = getattr(best, "year", 0) or 0

        if year and match_year and abs(year - match_year) > 1:

            self.logger.info(
                "rejected Crossref match for %r: year %d vs %d"
                % (title[:60], year, match_year)
            )

            return None

        return best

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

            # Crossref returns its best guess for any query, so the top hit for
            # a paper it does not hold is simply the nearest thing it does. Only
            # adopt it when the title genuinely matches, otherwise the citation
            # ends up pointing at an unrelated paper with a real DOI -- the
            # failure the verifier then reports as a mismatch.

            match = self._best_title_match(metadata.title, metadata.year)

            if match is not None:
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

    def _verify_citations(
        self,
        citations
    ):
        """Attach a verification record to every citation.

        Citations that fail are kept and flagged rather than dropped: a
        silently discarded citation is indistinguishable from one that was
        never found, which is how bad references go unnoticed.
        """

        if not citations:

            return citations

        results = self.verifier.verify_all(
            citations
        )

        for citation, result in zip(citations, results):

            # Preserve a claim verdict already recorded by the claim workflow.
            claim_supported = citation.verification.claim_supported

            existing_notes = (citation.verification.notes or "").strip()

            citation.verification = CitationVerification(
                claim_supported=claim_supported,
                **result
            )

            if existing_notes:

                citation.verification.notes = (
                    existing_notes
                    + " "
                    + citation.verification.notes
                ).strip()

        return citations

    def _build_response(
        self,
        citations
    ) -> str:

        if not citations:

            return "No citations could be generated."

        counts = {}

        for citation in citations:

            status = citation.verification.status

            counts[status] = counts.get(status, 0) + 1

        lines = [
            "Generated %d citation(s): %d verified, %d need attention."
            % (
                len(citations),
                counts.get("verified", 0),
                len(citations) - counts.get("verified", 0)
            )
        ]

        # Name the problem citations here rather than only on the Citations
        # page. A count alone reads as a statistic; a title reads as something
        # to fix, and the user should not have to change tabs to find out which.

        problems = [
            citation
            for citation in citations
            if citation.verification.status != "verified"
        ]

        if problems:

            lines.append("")
            lines.append("**Do not use these without checking:**")

            for citation in problems:

                status = citation.verification.status

                label = {
                    "mismatch": "DOI belongs to a different paper",
                    "unresolved": "no resolvable DOI",
                    "unverified": "could not be checked"
                }.get(status, status)

                detail = ""

                resolved = (
                    citation.verification.resolved_title or ""
                ).strip()

                if status == "mismatch" and resolved:

                    detail = " — the DOI points to \"%s\"" % resolved

                lines.append(
                    "- %s (%s%s)"
                    % (
                        citation.title or "Untitled",
                        label,
                        detail
                    )
                )

            lines.append("")
            lines.append(
                "Full details, including BibTeX, are on the Citations tab."
            )

        return "\n".join(lines)

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

                            bibtex=bibtex or ""

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
                    verdict = self._evaluate_claim_support(paper, claim_text)
                    if verdict["supports_claim"]:
                        supporting_papers.append((paper, verdict))

                if supporting_papers:
                    for paper, verdict in supporting_papers:

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
                                    bibtex=bibtex or "",
                                    claim=claim_text,
                                    verification=CitationVerification(
                                        claim_supported=True,
                                        notes=verdict.get("reason", "")
                                    )
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

        citations = self._verify_citations(
            citations
        )

        data = {

            "response": self._build_response(citations),

            "citations": citations,

            "count": len(citations)

        }

        state = self._update_state(
            state,
            data
        )

        return state, data