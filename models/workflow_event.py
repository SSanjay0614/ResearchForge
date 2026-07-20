from datetime import datetime

from pydantic import BaseModel, Field


class WorkflowEvent(BaseModel):

    agent: str

    action: str

    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )