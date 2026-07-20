from agents.manuscript_agent import ManuscriptAgent

from memory.state import ProjectState


agent = ManuscriptAgent()

state = ProjectState()

action = agent._decide_action(
    state,
    "Rewrite the abstract and make it more concise."
)

print(action)