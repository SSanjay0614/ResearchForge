from pydantic import BaseModel


class CrossrefPaper(BaseModel):

    title: str = ""

    authors: str = ""

    year: int = 0

    venue: str = ""

    doi: str = ""