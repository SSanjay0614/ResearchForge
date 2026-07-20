from pydantic import BaseModel, Field

from typing import Dict


class Manuscript(BaseModel):

    # -------------------------------------------------
    # Standard Sections
    # -------------------------------------------------

    title: str = ""

    abstract: str = ""

    introduction: str = ""

    literature_review: str = ""

    methodology: str = ""

    experiments: str = ""

    results: str = ""

    discussion: str = ""

    conclusion: str = ""

    # -------------------------------------------------
    # Custom Sections
    # -------------------------------------------------

    sections: Dict[str, str] = Field(
        default_factory=dict
    )

    # -------------------------------------------------
    # Complete LaTeX Source
    # -------------------------------------------------

    latex_source: str = ""