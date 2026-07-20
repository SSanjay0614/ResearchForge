from workflow.router import WorkflowRouter


router = WorkflowRouter()


queries = [

    "Help me plan a research project on fetal ECG.",

    "Find papers on fetal ECG signal extraction.",

    "Generate a literature review for these papers.",

    "Write the introduction section.",

    "Generate BibTeX for Attention Is All You Need.",

    "Help me respond to this reviewer comment."

]


for query in queries:

    action = router.route(
        query
    )

    print("=" * 80)

    print(query)

    print()

    print(action)

    print()