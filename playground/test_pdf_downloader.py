from tools.openalex_tool import OpenAlexTool
from tools.pdf_downloader import PDFDownloader


tool = OpenAlexTool()

papers = tool.run(
    "fetal ECG",
    max_results=10
)

paper = None

for p in papers:

    if p.metadata.pdf_url:

        paper = p
        break


if paper is None:

    print("No downloadable PDF found.")

else:

    print(paper.metadata.title)
    print()
    print(paper.metadata.pdf_url)

    downloader = PDFDownloader()

    path = downloader.run(
        paper.metadata.pdf_url,
        "paper.pdf"
    )

    print()
    print(path)