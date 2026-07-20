from agents.base_agent import BaseAgent

from memory.state import ProjectState

from tools.arxiv_tool import ArxivTool
from tools.openalex_tool import OpenAlexTool
from tools.paper_manager import PaperManager

from tools.pdf_downloader import PDFDownloader
from tools.pdf_reader import PDFReader
from tools.paper_analyzer import PaperAnalyzer


from config.prompts import LITERATURE_SYSTEM_PROMPT


class LiteratureAgent(BaseAgent):

    def __init__(self):

        super().__init__("Literature Intelligence Agent")

        self.arxiv = ArxivTool()

        self.openalex = OpenAlexTool()

        self.paper_manager = PaperManager()
        
        self.downloader = PDFDownloader()

        self.reader = PDFReader()

        self.analyzer = PaperAnalyzer()

    def _build_prompt(
        self,
        state: ProjectState,
        user_input: str
    ) -> str:

        return ""

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

        query = self._build_query(
            state,
            user_input
        )

        try:

            arxiv_papers = self.arxiv.run(
                query,
                max_results=10
            )

        except Exception as e:

            print(f"ArXiv failed: {e}")

            arxiv_papers = []


        try:

            openalex_papers = self.openalex.run(
                query,
                max_results=10
            )

        except Exception as e:

            print(f"OpenAlex failed: {e}")

            openalex_papers = []


        if not arxiv_papers and not openalex_papers:

            raise RuntimeError(
                "No literature sources available."
            )

        papers = self.paper_manager.run(
            arxiv_papers,
            openalex_papers
        )

        data = {

            "response": f"I found {len(papers)} relevant papers.",

            "papers": papers

        }

        state = self._update_state(
            state,
            data
        )
        
        state = self.analyze_papers(
            state
        )

        return state, data
    
    def analyze_papers(
        self,
        state: ProjectState,
        max_papers: int = 5
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