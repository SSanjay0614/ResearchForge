from memory.state import ProjectState

from agents.reviewer_agent import ReviewerAgent


state = ProjectState()

state.project_name = "PERFECG-Net"

state.topic = "Fetal ECG R-Peak Detection"

state.description = "Lightweight deep learning framework for fetal ECG R-peak detection."

state.manuscript.title = "PERFECG-Net"

state.manuscript.abstract = """
PERFECG-Net is a lightweight deep learning framework for fetal ECG R-peak detection designed for real-time wearable deployment.
"""

state.manuscript.introduction = """
Fetal ECG monitoring is challenging due to low SNR and maternal interference.
"""

state.manuscript.methodology = """
The proposed model uses a Physiologically-Informed Convolutional Bank (PICB) to capture fetal heart periodicity.
"""

state.manuscript.results = """
The proposed method achieves state-of-the-art performance while maintaining a lightweight architecture.
"""

state.literature_review = """
Recent work has focused on CNNs, U-Nets and Transformer-based architectures for fetal ECG extraction.
"""

state.research_gap = """
Existing methods are computationally expensive and rarely incorporate physiological priors.
"""


comment = """
The manuscript lacks deployment metrics such as inference latency, memory footprint and computational complexity.
"""

agent = ReviewerAgent()

state, data = agent.run(
    state,
    comment
)

print("=" * 80)
print("RESPONSE")
print("=" * 80)
print(data["response"])

print()

print("=" * 80)
print("MANUSCRIPT REVISION")
print("=" * 80)
print(data["manuscript_revision"])