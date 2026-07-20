from pydantic import BaseModel, Field
from typing import List


class PaperMetadata(BaseModel):

    title: str = ""

    authors: List[str] = Field(default_factory=list)

    abstract: str = ""

    year: int = 0

    venue: str = ""

    doi: str = ""

    url: str = ""

    pdf_url: str = ""

    local_pdf_path: str = ""

    citation_count: int = 0

    categories: List[str] = Field(default_factory=list)

    arxiv_id: str = ""