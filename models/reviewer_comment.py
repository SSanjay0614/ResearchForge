from pydantic import BaseModel


class ReviewerComment(BaseModel):

    comment: str = ""

    response: str = ""

    addressed: bool = False