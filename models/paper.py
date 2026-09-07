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

    # Verdict from the relevance check. Off-topic papers are dropped before
    # they reach the library unless DROP_IRRELEVANT_PAPERS is turned off, in
    # which case they are kept with this set to False and simply not analyzed.

    is_relevant: bool = True

    relevance_reason: str = ""

    # "full_text", "abstract" or "none" - how much of the paper the analysis
    # was based on, so the UI can be honest about depth.

    analysis_depth: str = "none"