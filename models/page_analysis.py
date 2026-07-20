from pydantic import BaseModel, Field

from typing import List


class PaperAnalysis(BaseModel):

    problem_statement: str = ""

    contribution: str = ""

    methodology: str = ""

    results: str = ""

    keywords: List[str] = Field(default_factory=list)