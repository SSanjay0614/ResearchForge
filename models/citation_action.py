from pydantic import BaseModel


class CitationAction(BaseModel):

    workflow: str

    title: str = ""

    query: str = ""