from typing import List, Optional

import requests
from models.crossref_paper import CrossrefPaper
from models.crossref_metadata import CrossrefMetadata
from tools.base_tool import BaseTool


class CrossrefTool(BaseTool):


    BASE_URL = "https://api.crossref.org/works"


    def __init__(self):

        super().__init__(
            "Crossref Tool"
        )

    def _get_authors(self, item: dict) -> List[str]:

        authors = []

        for author in item.get("author") or []:

            if not isinstance(author, dict):
                continue

            name = " ".join(
                part
                for part in [
                    author.get("given"),
                    author.get("family")
                ]
                if part
            )

            if name:
                authors.append(name)

        return authors

    def _get_publication_year(
        self,
        item: dict
    ) -> Optional[int]:

        for field in [
            "published-print",
            "published-online",
            "issued"
        ]:

            date = item.get(field) or {}

            date_parts = date.get("date-parts", [])

            if date_parts and date_parts[0]:
                return date_parts[0][0]

        return None

    def _to_metadata(
        self,
        item: dict
    ) -> CrossrefMetadata:

        titles = item.get("title") or []

        container_titles = item.get("container-title") or []

        return CrossrefMetadata(
            title=titles[0] if titles else None,
            authors=self._get_authors(item),
            doi=item.get("DOI"),
            url=item.get("URL"),
            publisher=item.get("publisher"),
            container_title=(
                container_titles[0]
                if container_titles
                else None
            ),
            publication_year=self._get_publication_year(item),
            volume=item.get("volume"),
            issue=item.get("issue"),
            pages=item.get("page"),
            type=item.get("type"),
            citation_count=item.get("is-referenced-by-count")
        )

    def run(
        self,
        query: str,
        rows: int = 5
    ):

        params = {
            "query.bibliographic": query,
            "sort": "relevance",
            "order": "desc",
            "rows": rows
        }

        response = requests.get(
            self.BASE_URL,
            params=params,
            timeout=30,
            headers={
                "User-Agent": "ResearchForge"
            }
        )

        response.raise_for_status()

        items = response.json()["message"]["items"]

        papers = []

        for item in items:

            title = ""

            if item.get("title"):

                title = item["title"][0]

            authors = []

            for author in item.get("author", []):

                given = author.get(
                    "given",
                    ""
                )

                family = author.get(
                    "family",
                    ""
                )

                authors.append(
                    f"{given} {family}".strip()
                )

            venue = ""

            if item.get("container-title"):

                venue = item["container-title"][0]

            year = 0

            published = (
                item.get("published-print")
                or item.get("published-online")
                or item.get("issued")
            )

            if published:

                year = published["date-parts"][0][0]

            papers.append(

                CrossrefPaper(

                    title=title,

                    authors=", ".join(authors),

                    year=year,

                    venue=venue,

                    doi=item.get(
                        "DOI",
                        ""
                    )

                )

            )

        return papers


    def get_bibtex(
        self,
        doi: str
    ) -> Optional[str]:

        if not doi:
            return None

        doi = doi.removeprefix("https://doi.org/")
        doi = doi.removeprefix("http://doi.org/")

        try:
            response = requests.get(
                "https://doi.org/{}".format(doi),
                timeout=30,
                headers={
                    "Accept": "application/x-bibtex",
                    "User-Agent": "ResearchForge"
                }
            )

            response.raise_for_status()

        except requests.RequestException:
            return None

        bibtex = response.text.strip()

        return bibtex or None
