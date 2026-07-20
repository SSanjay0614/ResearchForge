from pydantic import BaseModel


class ManuscriptAction(BaseModel):

    action: str

    section: str

    reason: str = ""