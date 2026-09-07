from pydantic import BaseModel, Field

from models.citation_verification import CitationVerification


class Citation(BaseModel):

    title: str = ""

    authors: str = ""

    year: int = 0

    doi: str = ""

    bibtex: str = ""

    citation: str = ""

    venue: str = ""

    # The claim this citation was found to support, when it came from a
    # claim-driven search. Empty for citations of project papers or titles.
    claim: str = ""

    # Result of checking the DOI and metadata. Defaults to an unverified
    # record, so citations loaded from older saved projects are reported as
    # unchecked rather than as verified.
    verification: CitationVerification = Field(
        default_factory=CitationVerification
    )
