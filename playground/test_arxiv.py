from tools.arxiv_tool import ArxivTool


tool = ArxivTool()

papers = tool.run(
    "fetal ECG deep learning",
    max_results=5
)


for paper in papers:

    print("-" * 60)

    print(paper.metadata.title)

    print(paper.metadata.authors)

    print(paper.metadata.year)