from pydantic import BaseModel


class ReviewerAction(BaseModel):

    strategy: str = ""

    reviewer_comment: str = ""