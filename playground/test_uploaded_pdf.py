from agents.literature_agent import LiteratureAgent

agent = LiteratureAgent()

analysis = agent.analyze_uploaded_pdf(
    pdf_path="paper.pdf"
)

print()

print("=" * 70)
print("PDF ANALYSIS")
print("=" * 70)

print(analysis)