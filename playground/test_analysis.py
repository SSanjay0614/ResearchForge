from memory.state import ProjectState

from agents.literature_agent import LiteratureAgent


state = ProjectState()

state.topic = "deep learning for natural language processing"

agent = LiteratureAgent()

state, data = agent.run(
    state,
    state.topic
)

print(data["response"])

print()

state = agent.analyze_papers(
    state,
    max_papers=1
)

print()

for paper in state.papers[:2]:

    print("=" * 70)

    print(paper.metadata.title)

    print()

    print(paper.analysis)