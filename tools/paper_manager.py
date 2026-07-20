import re

from tools.base_tool import BaseTool

from models.paper import Paper


class PaperManager(BaseTool):

    def __init__(self):

        super().__init__("Paper Manager")

    def _normalize_title(
        self,
        title: str
    ) -> str:

        title = title.lower()

        title = re.sub(
            r"[^a-z0-9 ]",
            "",
            title
        )

        return title.strip()
    
    def _normalize_doi(
        self,
        doi: str
    ) -> str:

        if not doi:
            return ""

        doi = doi.lower().strip()

        doi = doi.replace(
            "https://doi.org/",
            ""
        )

        doi = doi.replace(
            "http://doi.org/",
            ""
        )

        doi = doi.replace(
            "doi:",
            ""
        )

        return doi.strip()

    def run(
        self,
        *paper_lists: list[Paper]
    ) -> list[Paper]:

        papers: list[Paper] = []

        seen_doi = set()

        seen_titles = set()

        for paper_list in paper_lists:

            for paper in paper_list:

                doi = self._normalize_doi(
                    paper.metadata.doi
                )

                title = self._normalize_title(
                    paper.metadata.title
                )

                if doi:

                    if doi in seen_doi:
                        continue

                    seen_doi.add(doi)

                else:

                    if title in seen_titles:
                        continue

                    seen_titles.add(title)

                papers.append(paper)

        papers.sort(
            key=lambda paper: paper.metadata.citation_count,
            reverse=True
        )
        
        return papers