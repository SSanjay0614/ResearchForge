"""Transparent playground runner for LiteratureAgent.

Run from the repository root:
    conda run -n conda_env python playground/test_literature_transparent.py

The trace shows observable inputs and decisions made by the agent. It does not
attempt to expose hidden chain-of-thought from the language model.
"""

from time import perf_counter

from agents.literature_agent import LiteratureAgent
from memory.state import ProjectState


class TracedLiteratureAgent(LiteratureAgent):
    """LiteratureAgent with a human-readable execution trace."""

    def _build_query(self, state, user_input):
        query = super()._build_query(state, user_input)
        print(f"[DECISION] Search query: {query!r}")
        return query

    def _judge_relevance(self, paper, topic, user_input):
        title = getattr(getattr(paper, "metadata", None), "title", "") or "Untitled"
        print(f"[DECISION] Judging relevance: {title}")
        result = super()._judge_relevance(paper, topic, user_input)
        print(f"[DECISION] Relevance result: {'KEEP' if result else 'REJECT'}")
        return result

    def _reformulate_query(self, state, current_query, user_input):
        print(f"[DECISION] Too few relevant papers; reformulating {current_query!r}")
        query = super()._reformulate_query(state, current_query, user_input)
        print(f"[DECISION] Reformulated query: {query!r}")
        return query

    def _update_state(self, state, data):
        updated_state = super()._update_state(state, data)
        print(
            f"[STATE] status={updated_state.status!r}, "
            f"agent={updated_state.current_agent!r}, "
            f"papers={len(updated_state.papers)}"
        )
        return updated_state

    def run(self, state, user_input):
        print("\n" + "=" * 90)
        print(f"[USER] {user_input}")
        print(f"[STATE] topic={state.topic!r}, existing_papers={len(state.papers)}")

        # Wrap source and analysis calls to expose counts and failures while
        # retaining the production implementation and error handling.
        for source_name in ("arxiv", "openalex"):
            source = getattr(self, source_name)
            original_run = source.run

            def traced_source(query, max_results, *, _name=source_name, _run=original_run):
                started = perf_counter()
                try:
                    papers = _run(query, max_results=max_results)
                    print(
                        f"[TOOL] {_name}: returned {len(papers)} papers "
                        f"in {perf_counter() - started:.2f}s"
                    )
                    return papers
                except Exception as error:
                    print(f"[TOOL] {_name}: FAILED: {error}")
                    raise

            source.run = traced_source

        original_analyzer_run = self.analyzer.run

        def traced_analyzer(text):
            try:
                analysis = original_analyzer_run(text)
                print("[TOOL] paper_analyzer: abstract analyzed")
                return analysis
            except Exception as error:
                print(f"[TOOL] paper_analyzer: FAILED: {error}")
                raise

        self.analyzer.run = traced_analyzer

        started = perf_counter()
        try:
            updated_state, result = super().run(state, user_input)
        except Exception as error:
            print(f"[RESULT] FAILED after {perf_counter() - started:.2f}s: {error}")
            raise

        print(f"[RESULT] Completed in {perf_counter() - started:.2f}s")
        print(f"[RESULT] Response: {result.get('response', '')}")
        return updated_state, result


def print_papers(state):
    print("\n[FINAL PAPERS]")
    for index, paper in enumerate(state.papers, start=1):
        metadata = paper.metadata
        title = metadata.title or "Untitled"
        doi = metadata.doi or "No DOI"
        print(f"{index:02d}. {title}")
        print(f"    DOI: {doi}")
        print(f"    Has analysis: {bool(getattr(paper, 'analysis', None))}")


def main():
    state = ProjectState(
        project_name="Transparent Literature Test",
        topic="fetal ECG signal extraction",
        description="Trace literature search and relevance decisions.",
        status="planning",
    )
    agent = TracedLiteratureAgent()

    try:
        state, result = agent.run(
            state,
            "Find relevant papers on fetal ECG signal extraction and explain the search result.",
        )
    except Exception:
        print("\nThe run failed. The trace above identifies the last completed decision or tool call.")
        raise

    print_papers(state)
    print("\n[FINAL STATE]")
    print(f"status: {state.status}")
    print(f"current_agent: {state.current_agent}")
    print(f"chat_messages: {len(state.chat_history)}")
    print(f"workflow_events: {len(state.workflow_history)}")
    print(f"response_keys: {sorted(result.keys())}")


if __name__ == "__main__":
    main()
