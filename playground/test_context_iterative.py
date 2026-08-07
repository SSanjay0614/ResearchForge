import sys
import os
import json
from unittest.mock import MagicMock

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

mock_llm = MagicMock()
mock_llm.invoke = MagicMock(return_value=MagicMock(content='{}'))

import llm.ollama_provider as op
op.get_llm = MagicMock(return_value=mock_llm)

from memory.state import ProjectState
from models.paper import Paper, PaperMetadata, PaperAnalysis
from models.manuscript import Manuscript
from models.citation_action import CitationAction
from models.manuscript_action import ManuscriptAction
from models.reviewer_action import ReviewerAction

from agents.planning_agent import PlanningAgent
from agents.literature_agent import LiteratureAgent
from agents.synthesis_agent import SynthesisAgent
from agents.manuscript_agent import ManuscriptAgent
from agents.citation_agent import CitationAgent
from agents.reviewer_agent import ReviewerAgent


def test_planning_context():
    print("Testing PlanningAgent context builder...")
    agent = PlanningAgent()
    state = ProjectState(
        topic="Quantum Computing",
        description="Exploring Qiskit algorithms",
        objectives=["Obj 1", "Obj 2"],
        keywords=["quantum", "qiskit"]
    )
    context = agent._build_context(state)
    assert "Topic:" in context and "Quantum Computing" in context
    assert "Description:" in context and "Exploring Qiskit algorithms" in context
    assert "Objectives:" in context and "Obj 1" in context
    assert "Keywords:" in context and "quantum" in context
    print("✓ PlanningAgent context builder passed!")


def test_literature_context():
    print("Testing LiteratureAgent context builder...")
    agent = LiteratureAgent()
    paper = Paper(metadata=PaperMetadata(title="Quantum Paper 1", doi="10.1000/182"))
    state = ProjectState(
        topic="Quantum Computing",
        keywords=["quantum"],
        papers=[paper]
    )
    context = agent._build_context(state)
    assert "Quantum Computing" in context
    assert "quantum" in context
    assert "Quantum Paper 1" in context
    print("✓ LiteratureAgent context builder passed!")


def test_synthesis_context():
    print("Testing SynthesisAgent context builder...")
    agent = SynthesisAgent()
    paper = Paper(
        metadata=PaperMetadata(title="Paper Synthesis 1", abstract="Abstract text"),
        analysis=PaperAnalysis(problem_statement="Problem A", contribution="Contribution B", methodology="Method C", results="Result D")
    )
    state = ProjectState(papers=[paper])
    context = agent._build_context(state)
    assert "Paper Synthesis 1" in context
    assert "Problem A" in context
    assert "Contribution B" in context
    print("✓ SynthesisAgent context builder passed!")


def test_manuscript_context():
    print("Testing ManuscriptAgent context builder...")
    agent = ManuscriptAgent()
    state = ProjectState(
        topic="Neural Networks",
        objectives=["Improve accuracy"],
        literature_review="Previous work review...",
        research_gap="Lack of benchmarks",
        manuscript=Manuscript(title="Neural Networks Paper", introduction="Intro text...")
    )
    context = agent._build_context(state, target_section="introduction")
    assert "Neural Networks" in context
    assert "Improve accuracy" in context
    assert "Previous work review..." in context
    assert "Lack of benchmarks" in context
    assert "Intro text..." in context
    print("✓ ManuscriptAgent context builder passed!")


def test_citation_context():
    print("Testing CitationAgent context builder...")
    agent = CitationAgent()
    action = CitationAction(workflow="claim", query="transformer efficiency")
    context = agent._build_context(action, user_input="Transformers are efficient")
    assert "Transformers are efficient" in context or "transformer efficiency" in context
    print("✓ CitationAgent context builder passed!")


def test_reviewer_context():
    print("Testing ReviewerAgent context builder...")
    agent = ReviewerAgent()
    state = ProjectState(
        literature_review="Lit Review",
        research_gap="Gap text",
        manuscript=Manuscript(title="Reviewer Paper", methodology="Method text")
    )
    context = agent._build_context(state, reviewer_comment="Methodology lacks baseline")
    assert "Methodology lacks baseline" in context
    assert "Reviewer Paper" in context
    assert "Method text" in context
    assert "Lit Review" in context
    print("✓ ReviewerAgent context builder passed!")


def test_iterative_retry_logging():
    print("Testing retry logging in iterative workflows...")
    lit_agent = LiteratureAgent()
    lit_agent.logger = MagicMock()
    lit_agent._judge_relevance = MagicMock(return_value=False)
    dummy_paper = Paper(metadata=PaperMetadata(title="Dummy Title", abstract="Dummy abstract", doi="10.1/1"))
    lit_agent.arxiv.run = MagicMock(return_value=[dummy_paper])
    lit_agent.openalex.run = MagicMock(return_value=[])

    state = ProjectState(topic="Test Topic")
    lit_agent.run(state, "search test")
    lit_agent.logger.info.assert_called_with("insufficient relevant papers")
    print("✓ LiteratureAgent retry log passed!")

    manu_agent = ManuscriptAgent()
    manu_agent.logger = MagicMock()
    manu_agent._decide_action = MagicMock(return_value=ManuscriptAction(action="generate", section="introduction", reason=""))
    manu_agent._invoke_llm = MagicMock(side_effect=[
        {"section": "introduction", "latex": "\\section{Intro}"},
        {"acceptable": False, "critique": "Needs work", "revision_instructions": "Fix intro"},
        {"section": "introduction", "latex": "\\section{Revised Intro}"}
    ])
    manu_agent.run(state, "write intro")
    manu_agent.logger.info.assert_any_call("manuscript critique failed")
    print("✓ ManuscriptAgent retry log passed!")

    rev_agent = ReviewerAgent()
    rev_agent.logger = MagicMock()
    rev_agent._decide_strategy = MagicMock(return_value=ReviewerAction(strategy="writing_revision", reviewer_comment="Fix writing"))
    rev_agent._invoke_llm = MagicMock(side_effect=[
        {"response": "Initial response", "manuscript_revision": "Revision"},
        {"acceptable": False, "critique": "Not specific", "revision_instructions": "Be specific"},
        {"response": "Revised specific response", "manuscript_revision": "Specific revision"}
    ])
    rev_agent.run(state, "Fix writing")
    rev_agent.logger.info.assert_any_call("review response did not fully address concern")
    print("✓ ReviewerAgent retry log passed!")

    cit_agent = CitationAgent()
    cit_agent.logger = MagicMock()
    cit_agent._decide_workflow = MagicMock(return_value=CitationAction(workflow="claim", query="claim query"))
    cit_agent._evaluate_claim_support = MagicMock(return_value=False)
    cit_agent._reformulate_claim_query = MagicMock(return_value="new query")
    cit_agent.openalex.run = MagicMock(return_value=[dummy_paper])
    cit_agent.run(state, "test claim")
    cit_agent.logger.info.assert_any_call("insufficient supporting papers for claim")
    print("✓ CitationAgent retry log passed!")


if __name__ == "__main__":
    test_planning_context()
    test_literature_context()
    test_synthesis_context()
    test_manuscript_context()
    test_citation_context()
    test_reviewer_context()
    test_iterative_retry_logging()
    print("\nALL CONTEXT AND ITERATIVE RETRY LOGGING TESTS PASSED PERFECTLY!")
