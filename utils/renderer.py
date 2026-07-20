from models.citation import Citation
from models.paper import Paper


def render_response(state):

    response = state.last_response

    print()

    print("=" * 100)

    print("AGENT")

    print(state.current_agent)

    print()

    print("STATUS")

    print(state.status)

    print()

    # ---------------------------------------------------------
    # Planning
    # ---------------------------------------------------------

    if state.current_agent == "Planning Agent":

        print(response["response"])

        if "questions" in response:

            print()

            print("Questions")

            print("-" * 100)

            for question in response["questions"]:

                print(f"- {question}")

        return

    # ---------------------------------------------------------
    # Literature
    # ---------------------------------------------------------

    if state.current_agent == "Literature Intelligence Agent":

        print(response["response"])

        papers = response.get(
            "papers",
            state.papers
        )

        if papers:

            print()
            print("=" * 100)
            print("PAPERS")
            print("=" * 100)

            for i, paper in enumerate(
                papers,
                1
            ):

                print(f"{i}. {paper.metadata.title}")

                if paper.metadata.authors:

                    print(
                        f"Authors : {', '.join(paper.metadata.authors)}"
                    )

                print(
                    f"Year    : {paper.metadata.year}"
                )

                print(
                    f"Venue   : {paper.metadata.venue}"
                )

                if paper.metadata.doi:

                    print(
                        f"DOI     : {paper.metadata.doi}"
                    )

                print()

        return
    # ---------------------------------------------------------
    # Synthesis
    # ---------------------------------------------------------

    if state.current_agent == "Literature Synthesis Agent":

        print(response["response"])

        return

    # ---------------------------------------------------------
    # Manuscript
    # ---------------------------------------------------------

    if state.current_agent == "Manuscript Agent":

        if "section" in response:

            print(f"Section : {response['section']}")

            print()

        print(response["response"])

        return

    # ---------------------------------------------------------
    # Citation
    # ---------------------------------------------------------

    if state.current_agent == "Citation Agent":

        citations = response.get(
            "citations",
            state.citations
        )

        print(f"Generated {len(citations)} citation(s).")

        print()

        print("=" * 100)
        print("CITATIONS")
        print("=" * 100)

        for citation in citations:

            print(f"Title   : {citation.title}")

            print(f"Authors : {citation.authors}")

            print(f"Year    : {citation.year}")

            print(f"DOI     : {citation.doi}")

            print()

            print(citation.bibtex)

            print()

            print("-" * 100)

        return

    # ---------------------------------------------------------
    # Reviewer
    # ---------------------------------------------------------

    if state.current_agent == "Reviewer Agent":

        print("=" * 100)
        print("RESPONSE TO REVIEWER")
        print("=" * 100)
        print()

        print(
            response["response"]
        )

        revision = response.get(
            "manuscript_revision",
            ""
        )

        if revision:

            print()

            print("=" * 100)
            print("SUGGESTED MANUSCRIPT REVISION")
            print("=" * 100)
            print()

            print(revision)

        return