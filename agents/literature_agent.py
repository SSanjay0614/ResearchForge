from concurrent.futures import ThreadPoolExecutor

from agents.base_agent import BaseAgent

from memory.state import ProjectState

from tools.arxiv_tool import ArxivTool
from tools.openalex_tool import OpenAlexTool
from tools.paper_manager import PaperManager

from tools.pdf_downloader import PDFDownloader
from tools.pdf_reader import PDFReader
from tools.section_parser import SectionParser
from tools.paper_analyzer import PaperAnalyzer


from config.prompts import (
    LITERATURE_SYSTEM_PROMPT,
    PAPER_RELEVANCE_PROMPT,
    QUERY_REFORMULATION_PROMPT,
)

from config.settings import (
    DROP_IRRELEVANT_PAPERS,
    ENABLE_FULL_TEXT_ANALYSIS,
    FULL_TEXT_MAX_CHARS,
    MAX_ANALYZED_PAPERS,
    MAX_RETRIEVED_PAPERS,
    MAX_SEARCH_ITERATIONS,
    RELEVANCE_WORKERS,
    TARGET_RELEVANT_PAPERS,
)

DEPTH_LABELS = {
    "full_text": " (full paper)",
    "abstract": " (abstract only)"
}

ANALYSIS_FIELDS = [
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


class LiteratureAgent(BaseAgent):

    def __init__(self):

        super().__init__("Literature Intelligence Agent")

        self.arxiv = ArxivTool()

        self.openalex = OpenAlexTool()

        self.paper_manager = PaperManager()

        self.downloader = PDFDownloader()

        self.reader = PDFReader()

        self.parser = SectionParser()

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
    ) -> dict:

        title = getattr(paper.metadata, "title", "") or ""
        abstract = getattr(paper.metadata, "abstract", "") or ""

        if not abstract.strip():

            return {
                "is_relevant": False,
                "reason": "No abstract available to judge relevance."
            }

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

            return {
                "is_relevant": bool(data.get("is_relevant", True)),
                "reason": str(data.get("reason", "") or "")
            }

        except Exception as e:

            # A judging failure must not silently drop a paper.

            self.logger.warning(f"Relevance check failed for {title}: {e}")

            return {
                "is_relevant": True,
                "reason": "Relevance check unavailable; kept by default."
            }

    def _judge_all(
        self,
        papers: list,
        topic: str,
        user_input: str
    ) -> None:

        # Independent calls, so issue them concurrently. This is the single
        # biggest chunk of wall clock in a literature run.

        if not papers:

            return

        workers = max(1, min(RELEVANCE_WORKERS, len(papers)))

        with ThreadPoolExecutor(max_workers=workers) as pool:

            verdicts = list(
                pool.map(
                    lambda paper: self._judge_relevance(
                        paper,
                        topic,
                        user_input
                    ),
                    papers
                )
            )

        for paper, verdict in zip(papers, verdicts):

            paper.is_relevant = verdict["is_relevant"]

            paper.relevance_reason = verdict["reason"]

    def _has_analysis(
        self,
        paper
    ) -> bool:

        analysis = getattr(paper, "analysis", None)

        return bool(analysis) and any(
            getattr(analysis, field_name, None)
            for field_name in ANALYSIS_FIELDS
        )

    def _pdf_filename(
        self,
        paper
    ) -> str:

        stem = (
            getattr(paper.metadata, "arxiv_id", "")
            or getattr(paper.metadata, "doi", "")
            or getattr(paper.metadata, "title", "")
            or "paper"
        )

        return stem[:100] + ".pdf"

    def _acquire_text(
        self,
        paper
    ):
        """Best available text for a paper, plus the depth it represents."""

        abstract = (
            getattr(paper.metadata, "abstract", "") or ""
        ).strip()

        pdf_url = getattr(paper.metadata, "pdf_url", "") or ""

        title = getattr(paper.metadata, "title", "") or "Untitled"

        if ENABLE_FULL_TEXT_ANALYSIS and pdf_url:

            try:

                path = self.downloader.run(
                    pdf_url,
                    self._pdf_filename(paper)
                )

                sections = self.parser.run(
                    self.reader.run(path)
                )

                if self.parser.is_usable(sections):

                    return (
                        self.parser.analysis_text(
                            sections,
                            FULL_TEXT_MAX_CHARS
                        ),
                        "full_text"
                    )

                self.logger.info(
                    f"Full text for {title} had no parseable sections; using abstract."
                )

            except Exception as e:

                self.logger.info(
                    f"Full text unavailable for {title}: {e}"
                )

        return abstract, ("abstract" if abstract else "none")

    def _analyze(
        self,
        paper
    ) -> None:

        text, depth = self._acquire_text(paper)

        if not text:

            self.logger.warning(
                f"No text to analyze for {paper.metadata.title}"
            )

            return

        try:

            paper.analysis = self.analyzer.run(text)

            paper.analysis_depth = depth

        except Exception as e:

            self.logger.warning(
                f"Paper analysis failed for {paper.metadata.title}: {e}"
            )

    def _analyze_relevant(
        self,
        papers: list,
        budget: int
    ) -> int:

        # Only relevant papers earn an analysis, and they are taken in the
        # order the sources ranked them.

        candidates = [
            paper
            for paper in papers
            if paper.is_relevant
            and not self._has_analysis(paper)
        ]

        if ENABLE_FULL_TEXT_ANALYSIS:

            # Papers are ranked by citation count, which puts the
            # publisher-hosted ones first - and those are exactly the ones
            # whose PDFs are paywalled or bot-blocked. Prefer relevant papers
            # we can actually read in full, keeping the existing order within
            # each tier.

            def depth_tier(paper):

                if getattr(paper.metadata, "arxiv_id", ""):
                    return 0

                if getattr(paper.metadata, "pdf_url", ""):
                    return 1

                return 2

            candidates.sort(key=depth_tier)

        # A budget already spent arrives here as zero or less. Slicing with a
        # negative number would silently analyze all but the last few.

        targets = candidates[:budget] if budget > 0 else []

        if not targets:

            return 0

        workers = max(1, min(RELEVANCE_WORKERS, len(targets)))

        with ThreadPoolExecutor(max_workers=workers) as pool:

            list(
                pool.map(self._analyze, targets)
            )

        return sum(
            1
            for paper in targets
            if self._has_analysis(paper)
        )

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

        # Count analyses already in the project. Earlier versions wiped any
        # analysis past the budget, which threw away work the user had
        # already paid for.

        analyzed_papers = sum(
            1
            for paper in collected_papers
            if self._has_analysis(paper)
        )

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

            new_papers = []

            for paper in fetched_papers:

                doi = getattr(paper.metadata, "doi", "")
                title = getattr(paper.metadata, "title", "").lower()

                if (doi and doi in existing_dois) or (title and title in existing_titles):
                    continue

                new_papers.append(paper)

                if doi:
                    existing_dois.add(doi)
                if title:
                    existing_titles.add(title)

            self._judge_all(
                new_papers,
                state.topic or current_query,
                user_input
            )

            if DROP_IRRELEVANT_PAPERS:

                # Only relevant papers make it into the library. The off-topic
                # ones are named in the log rather than vanishing silently, so
                # a bad relevance verdict is still traceable.

                rejected = [
                    paper
                    for paper in new_papers
                    if not paper.is_relevant
                ]

                for paper in rejected:

                    self.logger.info(
                        "dropped as off-topic: %s (%s)"
                        % (
                            getattr(paper.metadata, "title", "") or "Untitled",
                            paper.relevance_reason or "no reason given"
                        )
                    )

                new_papers = [
                    paper
                    for paper in new_papers
                    if paper.is_relevant
                ]

            collected_papers.extend(new_papers)

            # Stop at the target rather than letting a generous iteration
            # overshoot it: every kept paper gets a full analysis, so an extra
            # paper is an extra PDF download and an extra long LLM call.

            if len(collected_papers) > TARGET_RELEVANT_PAPERS:

                collected_papers = collected_papers[:TARGET_RELEVANT_PAPERS]

            state.papers = collected_papers

            relevant_count = sum(
                1
                for paper in collected_papers
                if paper.is_relevant
            )

            self.logger.info(
                "iteration %d: %d new papers kept, %d relevant overall"
                % (iteration, len(new_papers), relevant_count)
            )

            if relevant_count >= TARGET_RELEVANT_PAPERS:
                break

            if iteration < MAX_SEARCH_ITERATIONS:
                self.logger.info(
                    "insufficient relevant papers (%d of %d); reformulating"
                    % (relevant_count, TARGET_RELEVANT_PAPERS)
                )
                current_query = self._reformulate_query(
                    state,
                    current_query,
                    user_input
                )

        # Analysis runs once, after the search has settled, so the budget is
        # spent on the relevant papers rather than on whatever arrived first.

        analyzed_papers += self._analyze_relevant(
            collected_papers,
            MAX_ANALYZED_PAPERS - analyzed_papers
        )

        state.papers = collected_papers

        relevant_total = sum(
            1
            for paper in collected_papers
            if paper.is_relevant
        )

        data = {

            "response": (
                "I kept %d relevant papers and analyzed %d of them.\n\n"
                % (relevant_total, analyzed_papers)
                + "Papers:\n"
                + "\n".join(
                    "- %s%s"
                    % (
                        paper.metadata.title or "Untitled Paper",
                        DEPTH_LABELS.get(
                            getattr(paper, "analysis_depth", ""),
                            ""
                            if paper.is_relevant
                            else " (not relevant to this topic)"
                        )
                    )
                    for paper in state.papers
                )
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

        self._analyze_relevant(
            state.papers,
            max_papers
        )

        return state

    def analyze_uploaded_pdf(
        self,
        pdf_path: str
    ):

        pages = self.reader.run(
            pdf_path
        )

        sections = self.parser.run(
            pages
        )

        if self.parser.is_usable(sections):

            return self.analyzer.run(
                self.parser.analysis_text(
                    sections,
                    FULL_TEXT_MAX_CHARS
                )
            )

        abstract = self.reader.extract_abstract(
            pdf_path
        )

        if not abstract:

            raise ValueError(
                "Could not extract usable text from this PDF."
            )

        return self.analyzer.run(
            abstract
        )
