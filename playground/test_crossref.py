from tools.openalex_tool import OpenAlexTool

tool = OpenAlexTool()

paper = tool.search_title(
    "Attention Is All You Need"
)

print(paper)

from tools.crossref_tool import CrossrefTool

crossref = CrossrefTool()

print(
    crossref.get_bibtex(
        paper.doi
    )
)