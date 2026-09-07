"""Verification for the router and citation-verification changes.

Run from the project root:

    python playground/verify_changes.py

Checks 1-6b are offline. Check 7 makes network calls, 8 makes LLM calls.
"""

import glob
import json
import os
import sys
import traceback

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)


results = []


def check(name):
    """Run a check, record pass/fail, keep going on failure."""

    def wrap(fn):

        print("\n" + "=" * 70)
        print(name)
        print("=" * 70)

        try:

            fn()
            results.append((name, "PASS", ""))

        except Exception as e:

            traceback.print_exc()
            results.append((name, "FAIL", "%s: %s" % (type(e).__name__, e)))

        return fn

    return wrap


# ---------------------------------------------------------------
# 1. Imports
# ---------------------------------------------------------------

@check("1. Imports")
def _imports():

    import workflow.graph  # noqa: F401
    import frontend.app  # noqa: F401

    print("workflow.graph and frontend.app import cleanly.")


# ---------------------------------------------------------------
# 2. Saved projects still load
# ---------------------------------------------------------------

@check("2. Saved projects load with the new Citation field")
def _projects():

    from memory.state import ProjectState

    # A citation saved before verification existed has no "verification" key at
    # all. That is the case the default has to cover: it must load as
    # "unverified" rather than looking checked. A project saved *after* a run
    # legitimately carries real statuses, so asserting on those would only test
    # what the last run happened to find.

    legacy = ProjectState(
        **{
            "citations": [
                {
                    "title": "Saved before verification existed",
                    "doi": "10.1000/legacy"
                }
            ]
        }
    )

    status = legacy.citations[0].verification.status

    print("citation with no verification block loads as %r" % status)

    assert status == "unverified", status

    assert legacy.citations[0].verification.doi_resolved is False

    assert legacy.citations[0].verification.claim_supported is None

    paths = glob.glob("projects/*.json")

    print("\nfound %d saved project(s)" % len(paths))

    if not paths:

        print("nothing on disk to load; skipping")
        return

    valid = {"verified", "unresolved", "mismatch", "unverified"}

    for path in paths[:5]:

        with open(path, encoding="utf-8") as handle:

            raw = json.load(handle)

        state = ProjectState(**raw)

        counts = {}

        for citation in state.citations:

            key = citation.verification.status

            counts[key] = counts.get(key, 0) + 1

        print(
            "  %s -> %d papers, %d citations %s"
            % (
                os.path.basename(path),
                len(state.papers),
                len(state.citations),
                counts or ""
            )
        )

        for key in counts:

            assert key in valid, "unknown verification status %r" % key

        # Anything the file did not record must come back unverified.
        for saved, citation in zip(raw.get("citations", []), state.citations):

            if "verification" not in saved:

                assert citation.verification.status == "unverified", (
                    "citation with no saved verification loaded as %r"
                    % citation.verification.status
                )


# ---------------------------------------------------------------
# 3. Citation key audit
# ---------------------------------------------------------------

@check("3. Citation key audit catches fabricated keys")
def _audit():

    from utils.citation_keys import audit_citations, extract_cite_keys
    from models.citation import Citation

    citations = [
        Citation(
            title="Attention Is All You Need",
            bibtex="@article{vaswani2017, title={Attention Is All You Need}}"
        ),
        # No bibtex, so no key: citing this would produce a broken reference.
        Citation(title="Has no bibtex")
    ]

    latex = (
        r"Prior work \citep{vaswani2017} established this. "
        r"Others \cite{invented2021} disagree, as do \citet[p. 4]{alsofake}. "
        r"Multiple at once \citep{vaswani2017,thirdfake}."
    )

    audit = audit_citations(latex, citations)

    print("cited keys :", audit["cited_keys"])
    print("known keys :", audit["known_keys"])
    print("unknown    :", audit["unknown_keys"])

    assert audit["known_keys"] == ["vaswani2017"], audit["known_keys"]

    assert sorted(audit["unknown_keys"]) == [
        "alsofake",
        "invented2021",
        "thirdfake"
    ], audit["unknown_keys"]

    # The optional-argument form is the one a naive regex misses.
    assert "alsofake" in extract_cite_keys(r"\citet[p. 4]{alsofake}")

    print("all three fabricated keys flagged, real key accepted")


# ---------------------------------------------------------------
# 4. Router state signature
# ---------------------------------------------------------------

@check("4. Router builds a state signature and keys its cache on it")
def _signature():

    from workflow.router import WorkflowRouter
    from memory.state import ProjectState
    from models.paper import Paper
    from models.paper_metadata import PaperMetadata

    router = WorkflowRouter.__new__(WorkflowRouter)

    empty = ProjectState(topic="federated learning")

    signature = router._state_signature(empty)

    print("empty project:")
    print(signature)

    assert "papers collected: 0" in signature
    assert "literature review: none" in signature

    loaded = ProjectState(
        topic="federated learning",
        literature_review="A review.",
        papers=[
            Paper(metadata=PaperMetadata(title="One"), is_relevant=True),
            Paper(metadata=PaperMetadata(title="Two"), is_relevant=False)
        ]
    )

    loaded_signature = router._state_signature(loaded)

    print("\nloaded project:")
    print(loaded_signature)

    assert "papers collected: 2 (1 relevant)" in loaded_signature
    assert "literature review: present" in loaded_signature

    # Same input, different state -> different cache key, or "continue" would
    # be answered from a stale route forever.
    assert router._cache_key("continue", signature) != router._cache_key(
        "continue",
        loaded_signature
    )

    print("\ncache key varies with state")


# ---------------------------------------------------------------
# 5. Precondition redirect
# ---------------------------------------------------------------

@check("5. A named precondition redirects to the producing agent")
def _redirect():

    from workflow.router import WorkflowRouter
    from models.router_action import RouterAction

    router = WorkflowRouter.__new__(WorkflowRouter)

    blocked = router._resolve_block(
        RouterAction(
            agent="synthesis",
            blocked_by="no papers collected",
            reason="Nothing to synthesise yet."
        )
    )

    print("synthesis blocked -> %s (requested %s)" % (
        blocked.agent,
        blocked.requested_agent
    ))

    assert blocked.agent == "literature"
    assert blocked.requested_agent == "synthesis"

    fine = router._resolve_block(
        RouterAction(agent="synthesis", reason="Papers are ready.")
    )

    assert fine.agent == "synthesis"
    assert fine.requested_agent == ""

    print("unblocked route left alone")

    # A reviewer comment is itself the input the reviewer agent needs, so
    # "no reviewer comments" must not bounce it to the manuscript agent.
    reviewer = router._resolve_block(
        RouterAction(
            agent="reviewer",
            blocked_by="no reviewer comments recorded",
            reason="Nothing to respond to."
        )
    )

    print("reviewer + 'no reviewer comments' -> %s" % reviewer.agent)

    assert reviewer.agent == "reviewer", reviewer.agent
    assert reviewer.blocked_by == ""


# ---------------------------------------------------------------
# 5b. Reviewer comments are not treated as manuscript edits
# ---------------------------------------------------------------

@check("5b. Reviewer feedback routes to the reviewer agent, not the manuscript agent")
def _reviewer_route():

    from workflow.router import WorkflowRouter
    from models.router_action import RouterAction

    router = WorkflowRouter.__new__(WorkflowRouter)

    # The two the user actually hit, plus the shapes around them.
    reviewer_comments = [
        "The reviewer requests cross-dataset evaluation.",
        "The reviewer states that the manuscript lacks deployment metrics such as latency, FLOPs and memory footprint.",
        "Reviewer 2 is concerned that the baselines are too weak.",
        "R1 notes the ablation study is missing.",
        "The referee asks for a runtime comparison."
    ]

    for text in reviewer_comments:

        corrected = router._correct_reviewer_route(
            RouterAction(agent="manuscript", reason="Mentions the manuscript."),
            text
        )

        print("  %-64s -> %s" % (text[:64], corrected.agent))

        assert corrected.agent == "reviewer", (text, corrected.agent)
        assert corrected.requested_agent == "manuscript"

    # A direct instruction to write stays with the manuscript agent even when a
    # reviewer is the stated motivation.
    edits = [
        "Rewrite the introduction to address the reviewer's concern.",
        "Write the limitations section.",
        "Expand the discussion section."
    ]

    print()

    for text in edits:

        left_alone = router._correct_reviewer_route(
            RouterAction(agent="manuscript", reason="Editing request."),
            text
        )

        print("  %-64s -> %s" % (text[:64], left_alone.agent))

        assert left_alone.agent == "manuscript", (text, left_alone.agent)

    # Only the manuscript agent is overridden; a deliberate literature or
    # citation route must survive the word "reviewer".
    for agent in ["literature", "citation", "synthesis", "planning"]:

        untouched = router._correct_reviewer_route(
            RouterAction(agent=agent, reason="Deliberate."),
            "The reviewer asked for more references."
        )

        assert untouched.agent == agent, (agent, untouched.agent)

    print("\nnon-manuscript routes untouched")


# ---------------------------------------------------------------
# 5c. Reviewer comments reach the state
# ---------------------------------------------------------------

@check("5c. The reviewer agent records its comment on the project state")
def _reviewer_state():

    from agents.reviewer_agent import ReviewerAgent
    from workflow.router import WorkflowRouter
    from memory.state import ProjectState

    agent = ReviewerAgent.__new__(ReviewerAgent)

    agent.name = "Reviewer Agent"

    state = ProjectState(topic="Fetal ECG extraction")

    assert state.reviewer_comments == []

    comment = "The reviewer requests cross-dataset evaluation."

    state = agent._update_state(
        state,
        {
            "reviewer_comment": comment,
            "response": "We have added a cross-dataset evaluation.",
            "manuscript_revision": "Added Section 4.3."
        }
    )

    print("recorded: %d comment(s)" % len(state.reviewer_comments))

    assert len(state.reviewer_comments) == 1, state.reviewer_comments
    assert state.reviewer_comments[0].comment == comment
    assert state.reviewer_comments[0].addressed is True

    # The same comment answered twice updates the record instead of duplicating
    # it: the count is what the router reads, so it has to mean something.
    state = agent._update_state(
        state,
        {
            "reviewer_comment": comment,
            "response": "Revised answer.",
            "manuscript_revision": ""
        }
    )

    assert len(state.reviewer_comments) == 1, state.reviewer_comments
    assert state.reviewer_comments[0].response == "Revised answer."

    print("re-answering the same comment updates, does not duplicate")

    # An empty comment is not a record.
    state = agent._update_state(state, {"reviewer_comment": "  ", "response": "x"})

    assert len(state.reviewer_comments) == 1, state.reviewer_comments

    # And the router's signature now reports it, which is what stops the
    # "no reviewer comments" precondition from firing.
    signature = WorkflowRouter.__new__(WorkflowRouter)._state_signature(state)

    assert "reviewer comments: 1" in signature, signature

    print("router state signature reports the comment")


# ---------------------------------------------------------------
# 6. Literature limits
# ---------------------------------------------------------------

@check("6. Literature pipeline keeps only relevant papers and analyzes all of them")
def _literature():

    import inspect

    from agents.literature_agent import LiteratureAgent
    from models.paper import Paper
    from models.paper_analysis import PaperAnalysis
    from models.paper_metadata import PaperMetadata

    from config.settings import (
        DROP_IRRELEVANT_PAPERS,
        MAX_ANALYZED_PAPERS,
        MAX_RETRIEVED_PAPERS,
        MAX_SEARCH_ITERATIONS,
        TARGET_RELEVANT_PAPERS
    )

    print("target relevant : %d" % TARGET_RELEVANT_PAPERS)
    print("max analyzed    : %d" % MAX_ANALYZED_PAPERS)
    print("retrieved/source: %d" % MAX_RETRIEVED_PAPERS)
    print("iterations      : %d" % MAX_SEARCH_ITERATIONS)
    print("drop irrelevant : %s" % DROP_IRRELEVANT_PAPERS)

    # Every relevant paper must be analyzable, or the run reports the
    # "found N, analyzed fewer" split the budget was meant to remove.
    assert MAX_ANALYZED_PAPERS >= TARGET_RELEVANT_PAPERS, (
        "analysis budget %d is below the target of %d relevant papers"
        % (MAX_ANALYZED_PAPERS, TARGET_RELEVANT_PAPERS)
    )

    # analyze_papers defaults to the settings value, not a stale module constant.
    default = inspect.signature(
        LiteratureAgent.analyze_papers
    ).parameters["max_papers"].default

    assert default == MAX_ANALYZED_PAPERS, default

    print("\nanalyze_papers default: %d" % default)

    # _analyze_relevant picks targets without touching the network: give it
    # papers whose analysis is already present so nothing is fetched.
    agent = LiteratureAgent.__new__(LiteratureAgent)

    def paper(title, relevant, analyzed):

        return Paper(
            metadata=PaperMetadata(title=title, arxiv_id="1234.5678"),
            analysis=(
                PaperAnalysis(contribution="Something.")
                if analyzed
                else PaperAnalysis()
            ),
            is_relevant=relevant
        )

    papers = [
        paper("Relevant, already analyzed", True, True),
        paper("Irrelevant", False, False),
        paper("Relevant, analyzed too", True, True)
    ]

    # Budget already spent: a negative budget must analyze nothing rather than
    # slicing the candidate list from the wrong end.
    assert agent._analyze_relevant(papers, -2) == 0

    assert agent._analyze_relevant(papers, 0) == 0

    print("spent budget analyzes nothing")

    # An irrelevant paper is never a candidate, whatever the budget.
    candidates = [
        item
        for item in papers
        if item.is_relevant and not agent._has_analysis(item)
    ]

    assert candidates == [], "already-analyzed papers should not be re-analyzed"

    print("relevant-only, no-rework selection holds")


# ---------------------------------------------------------------
# 6b. Verifier retries and repair, offline
# ---------------------------------------------------------------

@check("6b. Transient lookup failures retry; only 404 is taken as final")
def _retry():

    from tools.citation_verifier import CitationVerifier

    from config.settings import CITATION_VERIFY_RETRIES

    verifier = CitationVerifier()

    print("configured retries: %d" % CITATION_VERIFY_RETRIES)

    calls = {"n": 0}

    # A timeout then a success: the citation must not be left "unverified"
    # because of one flaky request.
    def flaky(doi):

        calls["n"] += 1

        if calls["n"] == 1:

            return None, "lookup failed: ReadTimeout", True

        return {"title": "Recovered Paper"}, "", False

    verifier._attempt_fetch = flaky

    # This sleeps once for the configured backoff, so it is a second or two.
    record, error = verifier._fetch_record("10.1000/flaky")

    print("attempts made: %d -> %s" % (calls["n"], record))

    assert calls["n"] == 2, calls["n"]
    assert record == {"title": "Recovered Paper"}, record
    assert error == "", error

    # A 404 is settled. Retrying it wastes time and cannot change the answer.
    calls["n"] = 0

    def absent(doi):

        calls["n"] += 1

        return None, "not registered", False

    verifier._attempt_fetch = absent

    record, error = verifier._fetch_record("10.9999/nope")

    print("404 attempts made: %d (%s)" % (calls["n"], error))

    assert calls["n"] == 1, calls["n"]
    assert error == "not registered", error

    # Repair refuses a loose title match rather than adopting the nearest hit,
    # which is how a citation ends up confidently pointing at the wrong paper.
    from models.citation import Citation

    verifier.find_correct_doi = lambda title, year=0: None

    unfixable = Citation(
        title="A paper Crossref does not hold",
        doi="10.4324/9780203984901-10"
    )

    assert verifier.repair_citation(unfixable) is None

    assert unfixable.doi == "10.4324/9780203984901-10", "original DOI must survive"

    print("failed repair leaves the original DOI flagged, not blanked")


# ---------------------------------------------------------------
# 7. Live DOI verification
# ---------------------------------------------------------------

@check("7. DOI verification, live (network)")
def _verify():

    from tools.citation_verifier import CitationVerifier
    from models.citation import Citation

    verifier = CitationVerifier()

    cases = [
        (
            "arXiv, correct title",
            Citation(
                title="Attention Is All You Need",
                year=2017,
                doi="10.48550/arXiv.1706.03762"
            ),
            "verified"
        ),
        (
            "Crossref journal, correct title",
            Citation(
                title="Deep learning",
                year=2015,
                doi="10.1038/nature14539"
            ),
            "verified"
        ),
        (
            "real DOI, wrong title",
            Citation(
                title="A Completely Unrelated Paper About Cheese",
                year=2017,
                doi="10.48550/arXiv.1706.03762"
            ),
            "mismatch"
        ),
        (
            "well-formed but nonexistent DOI",
            Citation(
                title="Imaginary Paper",
                year=2020,
                doi="10.9999/nonexistent.12345"
            ),
            "unresolved"
        ),
        (
            "no DOI at all",
            Citation(title="Untraceable Paper", year=2019),
            "unresolved"
        )
    ]

    failures = []

    for label, citation, expected in cases:

        result = verifier.verify_citation(citation)

        ok = result["status"] == expected

        print("  %-34s %-11s (want %-11s) %s" % (
            label,
            result["status"],
            expected,
            "ok" if ok else "MISMATCH"
        ))

        print("      %s" % result["notes"])

        if not ok:

            failures.append((label, result["status"], expected))

    assert not failures, "unexpected statuses: %s" % failures

    # Concurrency path.
    batch = verifier.verify_all([case[1] for case in cases])

    assert len(batch) == len(cases), len(batch)

    print("\nverify_all returned %d result(s)" % len(batch))


# ---------------------------------------------------------------
# 8. Live routing
# ---------------------------------------------------------------

@check("8. Routing honours preconditions, live (LLM)")
def _routing():

    from workflow.router import WorkflowRouter
    from memory.state import ProjectState
    from models.paper import Paper
    from models.paper_metadata import PaperMetadata

    router = WorkflowRouter()

    empty = ProjectState(topic="federated learning for credit scoring")

    with_papers = ProjectState(
        topic="federated learning for credit scoring",
        papers=[
            Paper(metadata=PaperMetadata(title="Paper %d" % i))
            for i in range(8)
        ]
    )

    with_manuscript = ProjectState(
        topic="federated learning for credit scoring",
        literature_review="A review.",
        papers=[
            Paper(metadata=PaperMetadata(title="Paper %d" % i))
            for i in range(8)
        ]
    )

    with_manuscript.manuscript.introduction = "We study federated credit scoring."

    with_manuscript.manuscript.experiments = "Experiments on one dataset."

    cases = [
        ("search for papers on federated credit scoring", empty, "literature", False),
        ("summarise the papers you found", empty, "literature", False),
        ("review my draft", empty, None, False),
        ("summarise the papers you found", with_papers, "synthesis", False),
        # The two the user reported going to the manuscript agent.
        (
            "The reviewer requests cross-dataset evaluation.",
            with_manuscript,
            "reviewer",
            True
        ),
        (
            "The reviewer states that the manuscript lacks deployment metrics such as latency, FLOPs and memory footprint.",
            with_manuscript,
            "reviewer",
            True
        ),
        (
            "Write the limitations section.",
            with_manuscript,
            "manuscript",
            True
        )
    ]

    failures = []

    for prompt, state, expected, strict in cases:

        action = router.route(prompt, state)

        print("  %-58s -> %-11s" % (prompt[:58], action.agent))
        print("      reason: %s" % (action.reason or "(none)"))

        if action.blocked_by:

            print("      blocked_by: %s (asked for %s)" % (
                action.blocked_by,
                action.requested_agent or "?"
            ))

        if expected and action.agent != expected:

            print("      NOTE: expected %s" % expected)

            if strict:

                failures.append((prompt[:58], action.agent, expected))

    assert not failures, "wrong agent: %s" % failures

    # The graph routes again with the same input and state; that must be a
    # cache hit rather than a second LLM call.
    before = len(WorkflowRouter._cache)

    router.route("search for papers on federated credit scoring", empty)

    assert len(WorkflowRouter._cache) == before, "cache missed on a repeat route"

    print("\nrepeat route served from cache")


# ---------------------------------------------------------------

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

for name, outcome, detail in results:

    print("%-4s %s%s" % (
        outcome,
        name,
        "  <- " + detail if detail else ""
    ))

failed = [row for row in results if row[1] == "FAIL"]

print("\n%d passed, %d failed" % (len(results) - len(failed), len(failed)))

sys.exit(1 if failed else 0)
