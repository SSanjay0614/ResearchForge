from pydantic import BaseModel


class Citation(BaseModel):

    title: str = ""

    authors: str = ""

    year: int = 0

    doi: str = ""

    bibtex: str = ""

    citation: str = ""
    
    venue: str = ""