from agents.planning_agent import PlanningAgent
from agents.literature_agent import LiteratureAgent
from agents.synthesis_agent import SynthesisAgent
from agents.manuscript_agent import ManuscriptAgent
from agents.citation_agent import CitationAgent
from agents.reviewer_agent import ReviewerAgent


planning = PlanningAgent()

literature = LiteratureAgent()

synthesis = SynthesisAgent()

manuscript = ManuscriptAgent()

citation = CitationAgent()

reviewer = ReviewerAgent()

def planning_node(state):

    state, data = planning.run(
        state,
        state.user_input
    )

    data["agent"] = planning.name
    state.last_response = data

    return state

def literature_node(state):

    state, data = literature.run(
        state,
        state.user_input
    )

    data["agent"] = literature.name
    state.last_response = data

    return state

def synthesis_node(state):

    state, data = synthesis.run(
        state,
        state.user_input
    )

    data["agent"] = synthesis.name
    state.last_response = data
    
    return state

def manuscript_node(state):

    state, data = manuscript.run(
        state,
        state.user_input
    )

    data["agent"] = manuscript.name
    state.last_response = data
    
    return state

def citation_node(state):

    state, data = citation.run(
        state,
        state.user_input
    )

    data["agent"] = citation.name
    state.last_response = data
    
    return state

def reviewer_node(state):

    state, data = reviewer.run(
        state,
        state.user_input
    )

    data["agent"] = reviewer.name
    state.last_response = data
    
    return state