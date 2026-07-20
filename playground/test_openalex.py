from tools.openalex_tool import OpenAlexTool


tool = OpenAlexTool()

papers = tool.run(
    "fetal ECG deep learning",
    max_results=5
)


for paper in papers:

    print("-" * 70)

    print("Title :", paper.metadata.title)

    print("Venue :", paper.metadata.venue)

    print("Year :", paper.metadata.year)

    print("Citations :", paper.metadata.citation_count)

    print("DOI :", paper.metadata.doi)