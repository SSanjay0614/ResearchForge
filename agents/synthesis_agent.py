from agents.base_agent import BaseAgent

from memory.state import ProjectState

from config.prompts import SYNTHESIS_SYSTEM_PROMPT


class SynthesisAgent(BaseAgent):


    def __init__(self):

        super().__init__(
            "Literature Synthesis Agent"
        )
        
    def _format_papers(
        self,
        state: ProjectState
    ) -> str:

        papers = []

        for i, paper in enumerate(state.papers, 1):

            if not paper.analysis:
                continue

            papers.append(
                f"""
    Paper {i}

    Title:
    {paper.metadata.title}

    Problem Statement:
    {paper.analysis.problem_statement}

    Contribution:
    {paper.analysis.contribution}

    Methodology:
    {paper.analysis.methodology}

    Results:
    {paper.analysis.results}
    """
            )

        return "\n\n".join(papers)
    
    def _build_prompt(
        self,
        state: ProjectState,
        user_input: str
    ) -> str:

        papers = self._format_papers(
            state
        )

        return f"""
    {SYNTHESIS_SYSTEM_PROMPT}

    Research Topic

    {state.topic}

    Analyzed Papers

    {papers}

    User Request

    {user_input}
    """
    
    def _update_state(
        self,
        state: ProjectState,
        data: dict
    ) -> ProjectState:

        state.current_agent = self.name

        state.status = "synthesis"

        state.literature_review = data["literature_review"]

        state.research_gap = data["research_gap"]

        response_text = data["literature_review"]
        research_gap = (data.get("research_gap") or "").strip()
        if research_gap:
            response_text = f"{response_text}\n\nResearch Gap\n\n{research_gap}"

        data["response"] = response_text

        return state
    
    
