from tools.arxiv_tool import ArxivTool

from tools.openalex_tool import OpenAlexTool

from tools.paper_manager import PaperManager


arxiv = ArxivTool()

openalex = OpenAlexTool()

manager = PaperManager()


papers = manager.run(

    arxiv.run(
        "fetal ECG",
        5
    ),

    openalex.run(
        "fetal ECG",
        5
    )

)

print(len(papers))

for paper in papers:

    print()

    print(paper.metadata.title)