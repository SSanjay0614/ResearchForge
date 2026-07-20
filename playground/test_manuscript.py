from memory.state import ProjectState

from agents.manuscript_agent import ManuscriptAgent


state = ProjectState()

state.project_name = "ResearchForge"

state.topic = "Fetal ECG Signal Processing"

state.description = (
    "Lightweight deep learning framework for fetal ECG R-peak detection."
)

state.literature_review = """
Deep learning methods such as CNNs, U-Nets and Transformers have been widely
used for fetal ECG extraction.
"""

state.research_gap = """
Existing methods are computationally expensive and rarely suitable for
wearable deployment.
"""

agent = ManuscriptAgent()

state, data = agent.run(
    state,
    "Generate an Ablation Study section."
)

print("=" * 80)
print("SECTION")
print("=" * 80)
print(data["section"])

print()

print("=" * 80)
print("LATEX")
print("=" * 80)
print(data["latex"])

print()

print("=" * 80)
print("CUSTOM SECTIONS")
print("=" * 80)
print(state.manuscript.sections)