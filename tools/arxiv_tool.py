import arxiv

from tools.base_tool import BaseTool

from models.paper import Paper
from models.paper_metadata import PaperMetadata


class ArxivTool(BaseTool):

    def __init__(self):

        super().__init__("Arxiv Tool")

    def run(
        self,
        query: str,
        max_results: int = 10
    ):

        client = arxiv.Client()

        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )

        papers: list[Paper] = []

        for result in client.results(search):

            metadata = PaperMetadata(

                title=result.title,

                authors=[
                    author.name
                    for author in result.authors
                ],

                abstract=result.summary,

                year=result.published.year,

                venue="arXiv",

                url=result.entry_id,

                pdf_url=result.pdf_url,

                categories=result.categories,

                arxiv_id=result.get_short_id()

            )

            papers.append(
                Paper(
                    metadata=metadata
                )
            )

        return papers