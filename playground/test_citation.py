from memory.state import ProjectState

from agents.literature_agent import LiteratureAgent
from agents.citation_agent import CitationAgent


state = ProjectState(

    topic="Fetal ECG",

    keywords=[
        "Deep Learning",
        "Signal Processing"
    ]

)

literature = LiteratureAgent()

citation = CitationAgent()


state, _ = literature.run(

    state,

    "Find papers on fetal ECG."

)

state, data = citation.run(

    state,

    "Generate BibTeX for all collected papers."

)

print()

print("=" * 80)

print("CITATIONS")

print("=" * 80)

for citation in state.citations:

    print()

    print(citation.title)

    print("-" * 60)

    print(citation.bibtex)