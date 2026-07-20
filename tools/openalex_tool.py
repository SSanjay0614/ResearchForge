import requests

from tools.base_tool import BaseTool

from models.paper import Paper
from models.paper_metadata import PaperMetadata
from models.crossref_paper import CrossrefPaper

class OpenAlexTool(BaseTool):

    BASE_URL = "https://api.openalex.org/works"

    def __init__(self):

        super().__init__("OpenAlex Tool")
    
    def _reconstruct_abstract(
        self,
        inverted_index
    ):

        if not inverted_index:
            return ""

        words = []

        for word, positions in inverted_index.items():

            for position in positions:

                words.append(
                    (position, word)
                )

        words.sort()

        return " ".join(
            word
            for _, word in words
        )

    def run(
        self,
        query: str,
        max_results: int = 10
    ):

        params = {
            "search": query,
            "per-page": max_results
        }

        response = requests.get(
            self.BASE_URL,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        papers = []

        for work in data.get("results", []):

            # -------------------------
            # Authors
            # -------------------------

            authors = []

            for authorship in work.get("authorships", []):

                author = authorship.get("author")

                if author:

                    authors.append(
                        author.get(
                            "display_name",
                            ""
                        )
                    )

            # -------------------------
            # Venue
            # -------------------------

            primary_location = work.get("primary_location") or {}

            source = primary_location.get("source") or {}

            venue = source.get(
                "display_name",
                ""
            )

            # -------------------------
            # IDs
            # -------------------------

            ids = work.get("ids") or {}

            doi = ids.get(
                "doi",
                ""
            )

            url = ids.get(
                "openalex",
                ""
            )

            # -------------------------
            # PDF
            # -------------------------

            pdf_url = ""

            for location in work.get("locations", []):

                pdf = location.get("pdf_url")

                if pdf:

                    pdf_url = pdf

                    break

            # -------------------------
            # Metadata
            # -------------------------

            metadata = PaperMetadata(

                title=work.get(
                    "display_name",
                    ""
                ),

                authors=authors,

                abstract=self._reconstruct_abstract(
                    work.get(
                        "abstract_inverted_index"
                    )
                ),

                year=work.get(
                    "publication_year"
                ) or 0,

                venue=venue,

                doi=doi,

                url=url,

                pdf_url=pdf_url,

                citation_count=work.get(
                    "cited_by_count",
                    0
                )
            )

            papers.append(
                Paper(
                    metadata=metadata
                )
            )

        return papers
    
    
    def search_title(
        self,
        title: str
    ):

        params = {
            "search": title,
            "per-page": 1
        }

        response = requests.get(
            self.BASE_URL,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        results = response.json().get(
            "results",
            []
        )

        if not results:

            return None

        work = results[0]

        authors = []

        for authorship in work.get(
            "authorships",
            []
        ):

            author = authorship.get(
                "author"
            )

            if author:

                authors.append(
                    author.get(
                        "display_name",
                        ""
                    )
                )

        venue = ""

        primary = work.get(
            "primary_location"
        ) or {}

        source = primary.get(
            "source"
        ) or {}

        venue = source.get(
            "display_name",
            ""
        )

        doi = ""

        ids = work.get(
            "ids"
        ) or {}

        doi = ids.get(
            "doi",
            ""
        )

        if doi.startswith(
            "https://doi.org/"
        ):

            doi = doi.replace(
                "https://doi.org/",
                ""
            )

        return CrossrefPaper(

            title=work.get(
                "display_name",
                ""
            ),

            authors=", ".join(
                authors
            ),

            year=work.get(
                "publication_year",
                0
            ),

            venue=venue,

            doi=doi
        )