from agents.base_agent import BaseAgent

from memory.state import ProjectState

from config.prompts import (
    MANUSCRIPT_SYSTEM_PROMPT,
    MANUSCRIPT_ACTION_PROMPT,
    MANUSCRIPT_CRITIQUE_PROMPT,
    MANUSCRIPT_INSTRUCTIONS_PROMPT,
    MANUSCRIPT_REVISION_PROMPT,
)

from models.manuscript_action import ManuscriptAction
from models.chat_message import ChatMessage
from models.workflow_event import WorkflowEvent

from utils.parser import parse_json
from utils.citation_keys import audit_citations

MAX_GENERATION_ITERATIONS = 2


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
        
    def _build_context(
        self,
        state: ProjectState,
        target_section: str = ""
    ) -> str:

        objectives = "\n".join(
            f"- {obj}"
            for obj in state.objectives
        ) or "None"

        relevant_content = "None"
        if target_section:
            section_key = target_section.strip().lower()
            manuscript = state.manuscript
            field_val = getattr(manuscript, section_key, None)
            if field_val:
                relevant_content = f"{target_section}\n{field_val}"
            elif manuscript.sections and section_key in manuscript.sections:
                relevant_content = f"{target_section}\n{manuscript.sections[section_key]}"

        return f"""
        Topic:
        {state.topic or "None"}

        Objectives:
        {objectives}

        Literature Review:
        {state.literature_review or "None"}

        Research Gap:
        {state.research_gap or "None"}

        Pre-Manuscript Information:
        {self._format_pre_manuscript_info(state)}

        Relevant Manuscript Section:
        {relevant_content}
        """

    def _format_pre_manuscript_info(self, state: ProjectState) -> str:
        info = getattr(state, "pre_manuscript_info", None) or {}
        if not info:
            return "None"
        return "\n".join(
            f"{label}: {info.get(key) or 'None'}"
            for key, label in [
                ("research_topic", "Research Topic"),
                ("research_description", "Research Description"),
                ("objectives", "Objectives"),
                ("literature_review", "Literature Review / Related Work"),
                ("methodology", "Methodology / Approach"),
                ("dataset_setup", "Dataset / Experimental Setup"),
                ("results_findings", "Results / Findings"),
                ("ablation_studies", "Ablation Studies"),
                ("additional_notes", "Additional Information / Notes"),
                ("target_venue", "Target Venue / Format"),
            ]
        )
        
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
        user_input: str,
        action: ManuscriptAction = None
    ) -> str:

        if action is None:
            action = self._decide_action(state, user_input)

        instructions = MANUSCRIPT_INSTRUCTIONS_PROMPT.format(
            action=action.action,
            section=action.section
        )

        context = self._build_context(
            state,
            action.section
        )

        return f"""
    {MANUSCRIPT_SYSTEM_PROMPT}

    {instructions}

    Manuscript Context:

    {context}

    User Request:

    {user_input}
    """

    def _critique_section(
        self,
        state: ProjectState,
        section_name: str,
        latex_content: str,
        user_input: str
    ) -> dict:

        context = self._build_context(state, section_name)

        prompt = f"""
        {MANUSCRIPT_CRITIQUE_PROMPT}

        Manuscript Context:
        {context}

        Target Section:
        {section_name}

        Draft LaTeX Content:
        {latex_content}

        User Request:
        {user_input}
        """

        try:
            return self._invoke_llm(prompt)
        except Exception:
            return {"acceptable": True, "critique": "", "revision_instructions": ""}

    def _build_revision_prompt(
        self,
        state: ProjectState,
        action: ManuscriptAction,
        initial_data: dict,
        critique_info: dict,
        user_input: str
    ) -> str:

        context = self._build_context(state, action.section)

        return MANUSCRIPT_REVISION_PROMPT.format(
            system_prompt=MANUSCRIPT_SYSTEM_PROMPT,
            context=context,
            action=action.action,
            section=action.section,
            initial_draft=initial_data.get("latex", ""),
            critique=critique_info.get("critique", ""),
            revision_instructions=critique_info.get("revision_instructions", ""),
            user_input=user_input
        )

    def _update_state(
        self,
        state: ProjectState,
        data: dict
    ) -> ProjectState:

        state.current_agent = self.name

        state.status = "manuscript"

        section = data.get("section", "").strip()
        latex = data.get("latex", "")

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

        elif section:

            state.manuscript.sections[
                section
            ] = latex

        data["response"] = latex

        # A fabricated citation key is easy to miss inside a wall of LaTeX, so
        # the warning rides along with the response the user actually reads.
        audit = data.get("citation_audit") or {}

        if audit.get("unknown_keys"):

            data["response"] = "%s\n\n⚠️ %s" % (
                latex,
                audit.get("message", "")
            )

        state.manuscript.latex_source = self._build_latex_source(
            state
        )

        return state

    def _audit_generated_citations(
        self,
        state: ProjectState,
        latex: str
    ) -> dict:
        """Check the draft's \\cite keys against the project bibliography.

        The model writes citation keys as part of the LaTeX, and nothing
        constrains it to keys that exist. An unmatched key is a fabricated
        reference, so it is reported rather than left to be discovered at
        compile time or, worse, at review.
        """

        audit = audit_citations(
            latex,
            state.citations
        )

        if audit["unknown_keys"]:

            audit["message"] = (
                "%d citation key(s) in this section are not in the project "
                "bibliography and may be fabricated: %s. Run the citation "
                "agent to find real sources, or remove them."
                % (
                    len(audit["unknown_keys"]),
                    ", ".join(audit["unknown_keys"])
                )
            )

        elif audit["cited_keys"]:

            audit["message"] = (
                "All %d citation key(s) resolve to the project bibliography."
                % len(audit["cited_keys"])
            )

        else:

            audit["message"] = ""

        return audit

    def run(
        self,
        state: ProjectState,
        user_input: str
    ):

        self.logger.info(
            f"{self.name} started. User Input: {user_input}"
        )

        action = self._decide_action(
            state,
            user_input
        )

        prompt = self._build_prompt(
            state,
            user_input,
            action=action
        )

        data = self._invoke_llm(
            prompt
        )

        section_name = data.get("section") or action.section or "Section"
        latex_content = data.get("latex", "")

        critique_info = self._critique_section(
            state,
            section_name,
            latex_content,
            user_input
        )

        if not critique_info.get("acceptable", True):

            self.logger.info("manuscript critique failed")

            revision_prompt = self._build_revision_prompt(
                state,
                action,
                data,
                critique_info,
                user_input
            )

            try:
                revised_data = self._invoke_llm(revision_prompt)
                if revised_data.get("latex"):
                    data = revised_data
            except Exception as e:
                self.logger.warning(f"Revision pass failed: {e}")

        audit = self._audit_generated_citations(
            state,
            data.get("latex", "")
        )

        data["citation_audit"] = audit

        if audit["unknown_keys"]:

            self.logger.warning(
                "manuscript cites %d key(s) not in the bibliography: %s"
                % (len(audit["unknown_keys"]), ", ".join(audit["unknown_keys"]))
            )

        state = self._update_state(
            state,
            data
        )

        data["agent"] = self.name
        state.last_response = data

        state.chat_history.append(
            ChatMessage(
                role="user",
                content=user_input
            )
        )

        state.chat_history.append(
            ChatMessage(
                role="assistant",
                agent=self.name,
                content=data.get("response", "")
            )
        )

        state.conversation_outputs.append(
            {
                "agent": self.name,
                "response": data.get("response", ""),
                "questions": data.get("questions", []),
                "papers": data.get("papers", []),
                "citations": data.get("citations", []),
                "manuscript_revision": data.get("manuscript_revision", ""),
            }
        )

        state.workflow_history.append(
            WorkflowEvent(
                agent=self.name,
                action="Completed"
            )
        )

        self.logger.info(
            f"{self.name} finished."
        )

        return state, data