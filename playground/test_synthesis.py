from agents.planning_agent import PlanningAgent
from agents.literature_agent import LiteratureAgent
from agents.synthesis_agent import SynthesisAgent

from memory.state import ProjectState

state = ProjectState()

planning = PlanningAgent()

literature = LiteratureAgent()

synthesis = SynthesisAgent()

state, _ = planning.run(
    state,
    "Deep learning for fetal ECG extraction"
)

state, _ = literature.run(
    state,
    state.topic
)

state = literature.analyze_papers(
    state,
    max_papers=3
)

state, _ = synthesis.run(
    state,
    "Write a literature review."
)

print("=" * 70)
print(state.literature_review)

print()

print("=" * 70)
print(state.research_gap)