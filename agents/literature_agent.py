from agents.base_agent import BaseAgent

from memory.state import ProjectState
from models.paper_analysis import PaperAnalysis

from tools.arxiv_tool import ArxivTool
from tools.openalex_tool import OpenAlexTool
from tools.paper_manager import PaperManager

from tools.pdf_downloader import PDFDownloader
from tools.pdf_reader import PDFReader
from tools.paper_analyzer import PaperAnalyzer


from config.prompts import (
    LITERATURE_SYSTEM_PROMPT,
    PAPER_RELEVANCE_PROMPT,
    QUERY_REFORMULATION_PROMPT,
)

MAX_SEARCH_ITERATIONS = 3
MAX_RETRIEVED_PAPERS = 5
TARGET_RELEVANT_PAPERS = 5
MAX_ANALYZED_PAPERS = 3


class LiteratureAgent(BaseAgent):

    def __init__(self):

        super().__init__("Literature Intelligence Agent")

        self.arxiv = ArxivTool()

        self.openalex = OpenAlexTool()

        self.paper_manager = PaperManager()
        
        self.downloader = PDFDownloader()

        self.reader = PDFReader()

        self.analyzer = PaperAnalyzer()

    def _build_context(
        self,
        state: ProjectState
    ) -> str:

        keywords = ", ".join(state.keywords) if state.keywords else "None"
        existing_titles = "\n".join(
            f"- {p.metadata.title} (DOI: {p.metadata.doi})"
            for p in state.papers
            if p.metadata and p.metadata.title
        ) or "None"

        return f"""
        Topic:
        {state.topic or "None"}

        Keywords:
        {keywords}

        Existing Papers:
        {existing_titles}
        """

    def _build_prompt(
        self,
        state: ProjectState,
        user_input: str
    ) -> str:

        return f"""
        {LITERATURE_SYSTEM_PROMPT}

        Literature Context:
        {self._build_context(state)}

        User Request:
        {user_input}
        """

    def _build_query(
        self,
        state: ProjectState,
        user_input: str
    ) -> str:

        if state.topic:

            return state.topic

        if state.keywords:

            return " ".join(
                state.keywords[:3]
            )

        return user_input

    def _judge_relevance(
        self,
        paper,
        topic: str,
        user_input: str
    ) -> bool:

        title = getattr(paper.metadata, "title", "") or ""
        abstract = getattr(paper.metadata, "abstract", "") or ""

        if not abstract.strip():
            return False

        prompt = f"""
        {PAPER_RELEVANCE_PROMPT}

        Topic:
        {topic}

        User Request:
        {user_input}

        Paper Title:
        {title}

        Paper Abstract:
        {abstract}
        """

        try:
            data = self._invoke_llm(prompt)
            return data.get("is_relevant", True)
        except Exception:
            return True

    def _reformulate_query(
        self,
        state: ProjectState,
        current_query: str,
        user_input: str
    ) -> str:

        prompt = f"""
        {QUERY_REFORMULATION_PROMPT}

        Literature Context:
        {self._build_context(state)}

        Previous Search Query:
        {current_query}

        User Request:
        {user_input}
        """

        try:
            data = self._invoke_llm(prompt)
            new_query = data.get("query", "").strip()
            return new_query if new_query else current_query
        except Exception:
            return f"{current_query} survey"

    def _update_state(
        self,
        state: ProjectState,
        data: dict
    ) -> ProjectState:

        state.current_agent = self.name

        state.status = "literature"

        state.papers = data["papers"]

        return state

    def run(
        self,
        state: ProjectState,
        user_input: str
    ):

        current_query = self._build_query(
            state,
            user_input
        )

        existing_dois = {
            p.metadata.doi for p in state.papers
            if p.metadata and p.metadata.doi
        }
        existing_titles = {
            p.metadata.title.lower() for p in state.papers
            if p.metadata and p.metadata.title
        }

        collected_papers = list(state.papers)
        analyzed_papers = 0
        analysis_fields = [
            "contribution",
            "problem_statement",
            "methodology",
            "results",
            "limitations",
            "future_work",
            "strengths",
            "weaknesses",
            "keywords",
            "important_findings",
        ]
        for paper in collected_papers:
            analysis = getattr(paper, "analysis", None)
            has_analysis = analysis and any(
                getattr(analysis, field_name, None)
                for field_name in analysis_fields
            )
            if has_analysis and analyzed_papers < MAX_ANALYZED_PAPERS:
                analyzed_papers += 1
            elif has_analysis:
                paper.analysis = PaperAnalysis()

        for iteration in range(1, MAX_SEARCH_ITERATIONS + 1):

            try:

                arxiv_papers = self.arxiv.run(
                    current_query,
                    max_results=MAX_RETRIEVED_PAPERS
                )

            except Exception as e:

                self.logger.warning(f"ArXiv failed: {e}")

                arxiv_papers = []

            try:

                openalex_papers = self.openalex.run(
                    current_query,
                    max_results=MAX_RETRIEVED_PAPERS
                )

            except Exception as e:

                self.logger.warning(f"OpenAlex failed: {e}")

                openalex_papers = []

            if not arxiv_papers and not openalex_papers and not collected_papers:

                raise RuntimeError(
                    "No literature sources available."
                )

            fetched_papers = self.paper_manager.run(
                arxiv_papers,
                openalex_papers
            )

            new_relevant_count = 0

            for paper in fetched_papers:

                doi = getattr(paper.metadata, "doi", "")
                title = getattr(paper.metadata, "title", "").lower()

                if (doi and doi in existing_dois) or (title and title in existing_titles):
                    continue

                self._judge_relevance(
                    paper,
                    state.topic or current_query,
                    user_input
                )

                abstract = getattr(paper.metadata, "abstract", "") or ""
                if abstract.strip() and analyzed_papers < MAX_ANALYZED_PAPERS:
                    try:
                        paper.analysis = self.analyzer.run(abstract)
                        analyzed_papers += 1
                    except Exception as e:
                        self.logger.warning(f"Paper analysis failed for {paper.metadata.title}: {e}")

                collected_papers.append(paper)
                if doi:
                    existing_dois.add(doi)
                if title:
                    existing_titles.add(title)
                new_relevant_count += 1

            state.papers = collected_papers

            if len(collected_papers) >= TARGET_RELEVANT_PAPERS:
                break

            if iteration < MAX_SEARCH_ITERATIONS:
                self.logger.info("insufficient relevant papers")
                current_query = self._reformulate_query(
                    state,
                    current_query,
                    user_input
                )

        data = {

            "response": "I found "
            f"{len(state.papers)} papers.\n\n"
            "Papers found:\n"
            + "\n".join(
                f"- {paper.metadata.title or 'Untitled Paper'}"
                for paper in state.papers
            ),

            "papers": state.papers

        }

        state = self._update_state(
            state,
            data
        )

        return state, data
    
    def analyze_papers(
        self,
        state: ProjectState,
        max_papers: int = MAX_ANALYZED_PAPERS
    ):

        analyzed = 0

        for paper in state.papers:

            if analyzed >= max_papers:
                break

            text = paper.metadata.abstract or ""

            if not text.strip():

                print(f"Skipping: {paper.metadata.title} (No abstract)")

                continue

            try:

                paper.analysis = self.analyzer.run(
                    text
                )

                analyzed += 1

                print(f"✓ {paper.metadata.title}")

            except Exception as e:

                print(f"✗ {paper.metadata.title}")

                print(e)

        return state
    
    def analyze_uploaded_pdf(
        self,
        pdf_path: str
    ):

        abstract = self.reader.extract_abstract(
            pdf_path
        )

        if not abstract:

            raise ValueError(
                "Could not extract abstract."
            )

        return self.analyzer.run(
            abstract
        )