from datetime import datetime

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):

    role: str

    content: str

    agent: str = ""

    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )