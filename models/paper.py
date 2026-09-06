from pydantic import BaseModel, Field

from models.paper_metadata import PaperMetadata
from models.paper_analysis import PaperAnalysis


class Paper(BaseModel):

    metadata: PaperMetadata = Field(
        default_factory=PaperMetadata
    )

    analysis: PaperAnalysis = Field(
        default_factory=PaperAnalysis
    )

    # Verdict from the relevance check. Irrelevant papers are still kept in
    # the project library, they just are not analyzed.

    is_relevant: bool = True

    relevance_reason: str = ""

    # "full_text", "abstract" or "none" - how much of the paper the analysis
    # was based on, so the UI can be honest about depth.

    analysis_depth: str = "none"