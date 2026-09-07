import re


# \cite{a,b}, \citep{...}, \citet{...}, \parencite{...}, and the starred and
# optional-argument forms LaTeX allows: \citep[see][p. 4]{key}.
CITE_PATTERN = re.compile(
    r"\\[a-zA-Z]*cite[a-zA-Z]*\*?\s*(?:\[[^\]]*\]\s*)*\{([^}]*)\}"
)

# @article{smith2019, ... -> smith2019
BIBTEX_KEY_PATTERN = re.compile(
    r"@\w+\s*\{\s*([^,\s}]+)"
)


def extract_cite_keys(latex: str):
    """Every citation key referenced in a LaTeX string, in order of appearance."""

    keys = []

    for group in CITE_PATTERN.findall(latex or ""):

        for key in group.split(","):

            key = key.strip()

            if key and key not in keys:

                keys.append(key)

    return keys


def extract_bibtex_key(bibtex: str) -> str:
    """The entry key of a BibTeX record, or "" if it has none."""

    match = BIBTEX_KEY_PATTERN.search(bibtex or "")

    return match.group(1).strip() if match else ""


def available_keys(citations):
    """Citation keys the project can actually resolve.

    A citation with no BibTeX has no key to cite, so it does not count as
    available: citing it would produce a broken reference.
    """

    keys = set()

    for citation in citations or []:

        key = extract_bibtex_key(
            getattr(citation, "bibtex", "")
        )

        if key:

            keys.add(key)

    return keys


def audit_citations(latex: str, citations):
    """Compare the keys a draft cites against the keys the project holds.

    Keys cited but not held are the fabrication case: the model invented a
    reference. Reported rather than removed, since the fix is to find the real
    source, not to delete the claim.
    """

    cited = extract_cite_keys(latex)

    known = available_keys(citations)

    unknown = [
        key
        for key in cited
        if key not in known
    ]

    return {
        "cited_keys": cited,
        "known_keys": sorted(known),
        "unknown_keys": unknown,
        "citation_count": len(cited)
    }
