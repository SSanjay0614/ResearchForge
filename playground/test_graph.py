from memory.state import ProjectState

from workflow.graph import graph

from utils.renderer import render_response


state = ProjectState()


queries = [

    "Help me plan a research project on fetal ECG.",

    "Find papers on fetal ECG signal extraction.",

    "Generate a literature review.",

    "Write the introduction section.",

    "Generate BibTeX for Attention Is All You Need.",

    "The reviewer says the manuscript lacks deployment metrics."

]


for query in queries:

    print()
    print("=" * 100)
    print("USER")
    print(query)
    print()

    state.user_input = query

    result = graph.invoke(
        state
    )

    state = ProjectState(
        **result
    )

    render_response(
        state
    )