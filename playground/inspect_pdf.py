from tools.pdf_reader import PDFReader


reader = PDFReader()

pages = reader.run("data/papers/paper.pdf")

text = "\n".join(pages)

print(text[:8000])