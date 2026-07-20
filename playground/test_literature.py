from agents.planning_agent import PlanningAgent
from agents.literature_agent import LiteratureAgent

from memory.state import ProjectState


state = ProjectState()

planner = PlanningAgent()

state, _ = planner.run(
    state,
    """
I want to build a multi-agent AI platform
for automating academic research workflows.
"""
)

literature = LiteratureAgent()

state, result = literature.run(
    state,
    "Find relevant papers."
)

print(result["response"])

print()

print(f"Retrieved: {len(state.papers)} papers")

print()

for paper in state.papers[:5]:

    print(paper.metadata.title)