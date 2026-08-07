from agents.base_agent import BaseAgent

from memory.state import ProjectState

from config.prompts import SYNTHESIS_SYSTEM_PROMPT


class SynthesisAgent(BaseAgent):


    def __init__(self):

        super().__init__(
            "Literature Synthesis Agent"
        )
        
    def _build_context(
        self,
        state: ProjectState
    ) -> str:

        formatted = []

        for i, paper in enumerate(state.papers, 1):
            title = getattr(paper.metadata, "title", "Untitled Paper")
            abstract = getattr(paper.metadata, "abstract", "")
            
            analysis_str = "No analysis available"
            if paper.analysis:
                analysis_str = f"""
                Problem Statement: {paper.analysis.problem_statement or 'N/A'}
                Contribution: {paper.analysis.contribution or 'N/A'}
                Methodology: {paper.analysis.methodology or 'N/A'}
                Results: {paper.analysis.results or 'N/A'}
                """.strip()

            formatted.append(
                f"""
                Paper {i}: {title}
                Abstract: {abstract}
                Analysis:
                {analysis_str}
                """
            )

        return "\n\n".join(formatted) if formatted else "No papers collected yet."
    
    def _build_prompt(
        self,
        state: ProjectState,
        user_input: str
    ) -> str:

        context = self._build_context(
            state
        )

        return f"""
        {SYNTHESIS_SYSTEM_PROMPT}

        Research Topic:
        {state.topic}

        Papers and Analyses Context:
        {context}

        User Request:
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
    
    
