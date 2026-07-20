from pydantic import BaseModel, Field

from typing import List


class PaperAnalysis(BaseModel):

    contribution: str = ""

    problem_statement: str = ""

    methodology: str = ""

    datasets: List[str] = Field(
        default_factory=list
    )

    evaluation_metrics: List[str] = Field(
        default_factory=list
    )

    results: str = ""

    limitations: str = ""

    future_work: str = ""

    strengths: List[str] = Field(
        default_factory=list
    )

    weaknesses: List[str] = Field(
        default_factory=list
    )

    keywords: List[str] = Field(
        default_factory=list
    )

    important_findings: List[str] = Field(
        default_factory=list
    )