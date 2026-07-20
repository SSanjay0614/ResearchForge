from agents.base_agent import BaseAgent

from memory.state import ProjectState

from config.prompts import MANUSCRIPT_SYSTEM_PROMPT

from models.manuscript_action import ManuscriptAction

from config.prompts import MANUSCRIPT_ACTION_PROMPT

from models.manuscript_action import ManuscriptAction

from utils.parser import parse_json

class ManuscriptAgent(BaseAgent):


    def __init__(self):

        super().__init__(
            "Manuscript Agent"
        )
    
    def _decide_action(
        self,
        state: ProjectState,
        user_input: str
    ) -> ManuscriptAction:
        

        prompt = f"""
    {MANUSCRIPT_ACTION_PROMPT}

    User Request

    {user_input}
    """

        response = self.llm.invoke(
            prompt
        )

        data = parse_json(
            response.content
        )

        return ManuscriptAction(
            **data
        )
        
    def _build_manuscript_context(
        self,
        state: ProjectState
    ) -> str:

        sections = []

        manuscript = state.manuscript

        if manuscript.title:
            sections.append(f"Title\n{manuscript.title}")

        if manuscript.abstract:
            sections.append(f"Abstract\n{manuscript.abstract}")

        if manuscript.introduction:
            sections.append(f"Introduction\n{manuscript.introduction}")

        if manuscript.methodology:
            sections.append(f"Methodology\n{manuscript.methodology}")

        if manuscript.experiments:
            sections.append(f"Experiments\n{manuscript.experiments}")

        if manuscript.results:
            sections.append(f"Results\n{manuscript.results}")

        if manuscript.conclusion:
            sections.append(f"Conclusion\n{manuscript.conclusion}")

        return "\n\n".join(sections)
        
    def _build_latex_source(
        self,
        state: ProjectState
    ):

        manuscript = state.manuscript

        sections = []

        if manuscript.title:
            sections.append(manuscript.title)

        if manuscript.abstract:
            sections.append(manuscript.abstract)

        if manuscript.introduction:
            sections.append(manuscript.introduction)

        if manuscript.literature_review:
            sections.append(manuscript.literature_review)

        if manuscript.methodology:
            sections.append(manuscript.methodology)

        if manuscript.experiments:
            sections.append(manuscript.experiments)

        if manuscript.results:
            sections.append(manuscript.results)

        if manuscript.discussion:
            sections.append(manuscript.discussion)

        if manuscript.conclusion:
            sections.append(manuscript.conclusion)

        # -----------------------------------------
        # Custom Sections
        # -----------------------------------------

        for section_name, content in manuscript.sections.items():

            if not content.strip():
                continue

            sections.append(
                f"\\section{{{section_name}}}\n\n{content}"
            )

        return "\n\n".join(
            sections
        )

    def _build_prompt(
        self,
        state: ProjectState,
        user_input: str
    ) -> str:

        action = self._decide_action(
            state,
            user_input
        )

        objectives = "\n".join(
            f"- {obj}"
            for obj in state.objectives
        )
        
        instructions = f"""
        Action:
        {action.action}

        Target Section:
        {action.section}

        Instructions:

        - If action is "generate", create the section from scratch.
        - If action is "rewrite", completely rewrite the existing section according to the user's request.
        - If action is "improve", improve the existing section while preserving its meaning and structure.
        - If action is "continue", continue writing from the existing section without repeating previous content.
        """

        manuscript = self._build_manuscript_context(
            state
        )

        return f"""
    {MANUSCRIPT_SYSTEM_PROMPT}

    {instructions}

    Project Topic

    {state.topic}

    Objectives

    {objectives}

    Literature Review

    {state.literature_review}

    Research Gap

    {state.research_gap}

    Existing Manuscript

    {manuscript}

    User Request

    {user_input}
    """
    
    def _update_state(
        self,
        state: ProjectState,
        data: dict
    ) -> ProjectState:

        state.current_agent = self.name

        state.status = "manuscript"

        section = data["section"].strip()

        latex = data["latex"]

        section_key = section.lower()

        if section_key == "title":
            state.manuscript.title = latex

        elif section_key == "abstract":
            state.manuscript.abstract = latex

        elif section_key == "introduction":
            state.manuscript.introduction = latex

        elif section_key == "literature review":
            state.manuscript.literature_review = latex

        elif section_key == "methodology":
            state.manuscript.methodology = latex

        elif section_key == "experiments":
            state.manuscript.experiments = latex

        elif section_key == "results":
            state.manuscript.results = latex

        elif section_key == "discussion":
            state.manuscript.discussion = latex

        elif section_key == "conclusion":
            state.manuscript.conclusion = latex

        else:

            state.manuscript.sections[
                section
            ] = latex

        data["response"] = latex

        state.manuscript.latex_source = self._build_latex_source(
            state
        )

        return state