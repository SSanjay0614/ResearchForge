from pydantic import BaseModel, Field
from typing import List, Dict

from models.paper import Paper
from models.citation import Citation
from models.reviewer_comment import ReviewerComment
from models.manuscript import Manuscript
from models.chat_message import ChatMessage
from models.workflow_event import WorkflowEvent

class ProjectState(BaseModel):

    # ---------------------------------
    # Project Information
    # ---------------------------------

    project_name: str = ""

    topic: str = ""
    
    description: str = ""

    objectives: List[str] = Field(default_factory=list)

    keywords: List[str] = Field(default_factory=list)

    status: str = "planning"

    current_agent: str = ""
    
    user_input: str = ""
    
    last_response: dict = Field(
        default_factory=dict
    )

    reviewer_response: dict = Field(
        default_factory=dict
    )

    conversation_outputs: List[dict] = Field(
        default_factory=list
    )
    
    needs_more_information: bool = False


    # ---------------------------------
    # Literature
    # ---------------------------------

    papers: List[Paper] = Field(default_factory=list)

    literature_review: str = ""

    research_gap: str = ""


    # ---------------------------------
    # Manuscript
    # ---------------------------------

    manuscript: Manuscript = Field(default_factory=Manuscript)

    citations: List[Citation] = Field(default_factory=list)


    # ---------------------------------
    # Review Process
    # ---------------------------------

    reviewer_comments: List[ReviewerComment] = Field(default_factory=list)


    # ---------------------------------
    # Memory
    # ---------------------------------

    chat_history: List[ChatMessage] = Field(
    default_factory=list
    )

    workflow_history: List[WorkflowEvent] = Field(
        default_factory=list
    )