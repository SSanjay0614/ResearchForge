from pydantic import BaseModel


class RouterAction(BaseModel):

    agent: str = ""