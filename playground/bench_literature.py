"""End-to-end literature agent timing. Backend comes from the environment.

    OLLAMA_MODEL=gemma4:31b-cloud python playground/bench_literature.py
    LLM_BACKEND=gemini          python playground/bench_literature.py
"""

import sys
import time
import warnings

warnings.filterwarnings("ignore")

from agents.literature_agent import LiteratureAgent
from llm.ollama_provider import ollama_provider
from memory.state import ProjectState


def main():
    topic = sys.argv[1] if len(sys.argv) > 1 else "interpretable machine learning for credit scoring"

    state = ProjectState(project_name="bench", topic=topic, description=topic)
    state.keywords = ["interpretable machine learning", "credit scoring"]

    agent = LiteratureAgent()

    print("backend: %s" % ollama_provider.describe())

    started = time.time()
    state, data = agent.run(state, "find recent papers on " + topic)
    wall = time.time() - started

    print("wall clock       : %.1fs (%.1f min)" % (wall, wall / 60))
    print("papers collected : %d" % len(state.papers))
    print("judged relevant  : %d" % sum(1 for p in state.papers if p.is_relevant))
    print("analyzed         : %d" % sum(1 for p in state.papers if p.analysis.contribution))
    print("  from full text : %d" % sum(1 for p in state.papers if p.analysis_depth == "full_text"))
    print("  from abstract  : %d" % sum(1 for p in state.papers if p.analysis_depth == "abstract"))

    for paper in state.papers:
        if paper.analysis.contribution:
            print()
            print("  %s [%s]" % (paper.metadata.title[:64], paper.analysis_depth))
            print("    datasets : %s" % (paper.analysis.datasets or "-"))
            print("    metrics  : %s" % (paper.analysis.evaluation_metrics or "-"))
            print("    results  : %s" % (paper.analysis.results or "-")[:150])


if __name__ == "__main__":
    main()
