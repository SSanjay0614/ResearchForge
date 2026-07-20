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