from tools.pdf_reader import PDFReader


reader = PDFReader()

pages = reader.run(
    "data/papers/paper.pdf"
)

print(len(pages))

print()

print(pages[0][:3000])