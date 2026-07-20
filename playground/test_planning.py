from agents.planning_agent import PlanningAgent
from memory.state import ProjectState


state = ProjectState()

agent = PlanningAgent()


state, result = agent.run(
    state,
    """
I want to build a multi-agent AI platform that automates
academic research workflows using specialized AI agents.
"""
)

print("=" * 60)
print("LLM Response")
print("=" * 60)

print(result["response"])

print("\n")

print("=" * 60)
print("Updated State")
print("=" * 60)

print(state.model_dump())