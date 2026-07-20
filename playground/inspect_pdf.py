from tools.pdf_reader import PDFReader


reader = PDFReader()

text = reader.run("data/papers/paper.pdf")

print(text[:8000])