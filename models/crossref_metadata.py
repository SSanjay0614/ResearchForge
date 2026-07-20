from typing import List, Optional

from pydantic import BaseModel, Field


class CrossrefMetadata(BaseModel):

    title: Optional[str] = None

    authors: List[str] = Field(default_factory=list)

    doi: Optional[str] = None

    url: Optional[str] = None

    publisher: Optional[str] = None

    container_title: Optional[str] = None

    publication_year: Optional[int] = None

    volume: Optional[str] = None

    issue: Optional[str] = None

    pages: Optional[str] = None

    type: Optional[str] = None

    citation_count: Optional[int] = None
