from tools.pdf_reader import PDFReader

from tools.section_parser import SectionParser


reader = PDFReader()

parser = SectionParser()


text = reader.run(
    "data/papers/paper.pdf"
)

sections = parser.run(text)

print(sections.keys())