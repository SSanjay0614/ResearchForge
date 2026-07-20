from pydantic import BaseModel
from typing import List


class Project(BaseModel):

    name: str = ""

    topic: str = ""

    objectives: List[str] = []

    keywords: List[str] = []