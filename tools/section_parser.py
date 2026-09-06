import re

from tools.base_tool import BaseTool


# Canonical section name -> surface forms seen in real papers.
# Longest aliases must come first within a list so that
# "results and discussion" wins over "results".

SECTION_ALIASES = {

    "abstract": [
        "abstract"
    ],

    "introduction": [
        "introduction",
        "intro"
    ],

    "related work": [
        "related works",
        "related work",
        "literature review",
        "prior work",
        "background and related work",
        "background"
    ],

    "methodology": [
        "proposed methodology",
        "proposed method",
        "proposed approach",
        "system architecture",
        "problem formulation",
        "materials and methods",
        "methodology",
        "method",
        "methods",
        "approach",
        "our model",
        "model"
    ],

    "experiments": [
        "experimental evaluation",
        "experimental settings",
        "experimental setup",
        "implementation details",
        "evaluation metrics",
        "experiments",
        "experiment",
        "datasets",
        "dataset"
    ],

    "results": [
        "results and discussion",
        "results and analysis",
        "ablation study",
        "results",
        "evaluation",
        "findings",
        "ablation"
    ],

    "discussion": [
        "discussion",
        "analysis"
    ],

    "limitations": [
        "limitations and future work",
        "threats to validity",
        "limitations"
    ],

    "conclusion": [
        "conclusion and future work",
        "conclusions and future work",
        "concluding remarks",
        "conclusions",
        "conclusion"
    ],

    "future work": [
        "future work",
        "future directions"
    ],

    "references": [
        "references",
        "bibliography"
    ],

    "acknowledgements": [
        "acknowledgements",
        "acknowledgments",
        "acknowledgement",
        "acknowledgment"
    ],

    "appendix": [
        "supplementary material",
        "supplementary",
        "appendices",
        "appendix"
    ],
}


# Optional leading section number: "1", "2.3", "IV", each with optional . ) :
# Also tolerates the "Section" / "Chapter" word some templates emit.

NUMBER_PREFIX = r"(?:(?:section|chapter)\s+)?(?:(?:\d+(?:\.\d+)*|[IVXLCDM]{1,6})\s*[.):]?\s+)?"


# Sections worth sending to the analyzer, in the order they should appear,
# with a per-section character cap so one long section cannot crowd out
# the rest of the paper.

ANALYSIS_SECTIONS = [
    ("abstract", 3000),
    ("introduction", 7000),
    ("methodology", 12000),
    ("experiments", 8000),
    ("results", 8000),
    ("discussion", 4000),
    ("limitations", 2000),
    ("conclusion", 3000),
    ("future work", 1500),
]


# Never sent to the analyzer: pure overhead that is mostly citation strings.

ANALYSIS_EXCLUDED = [
    "related work",
    "references",
    "acknowledgements",
    "appendix",
]


class SectionParser(BaseTool):

    def __init__(self):

        super().__init__(
            "Section Parser"
        )

        self.pattern = self._build_pattern()

    def _build_pattern(self):

        alternatives = []

        for aliases in SECTION_ALIASES.values():

            for alias in aliases:

                alternatives.append(
                    re.escape(alias).replace(r"\ ", r"\s+")
                )

        return re.compile(
            r"(?im)^[ \t]*" +
            NUMBER_PREFIX +
            r"(" + "|".join(alternatives) + r")" +
            r"[ \t]*[:.]?[ \t]*$"
        )

    def _canonical(
        self,
        heading: str
    ) -> str:

        heading = re.sub(r"\s+", " ", heading.strip().lower())

        for name, aliases in SECTION_ALIASES.items():

            if heading in aliases:

                return name

        return heading

    def _as_text(
        self,
        text
    ) -> str:

        # PDFReader.run() hands back a list of pages, not a string.

        if isinstance(text, (list, tuple)):

            return "\n".join(
                str(page)
                for page in text
            )

        return text or ""

    def run(
        self,
        text
    ) -> dict:

        text = self._as_text(text)

        matches = list(
            self.pattern.finditer(text)
        )

        # Everything from the first "References" heading onward is one blob,
        # otherwise stray title-like lines in the bibliography get parsed
        # as body sections.

        tail = None

        for i, match in enumerate(matches):

            if self._canonical(match.group(1)) in ("references", "acknowledgements"):

                tail = i

                break

        sections = {}

        for i, match in enumerate(matches):

            if tail is not None and i > tail:

                continue

            name = self._canonical(
                match.group(1)
            )

            start = match.end()

            if tail is not None and i == tail:

                end = len(text)

            elif i + 1 < len(matches):

                end = matches[i + 1].start()

            else:

                end = len(text)

            body = text[start:end].strip()

            if not body:

                continue

            sections[name] = (
                sections[name] + "\n\n" + body
                if name in sections
                else body
            )

        return sections

    def is_usable(
        self,
        sections: dict
    ) -> bool:

        # Worth a full-text analysis only if the parser found the abstract
        # plus at least one substantive body section.

        body = [
            name
            for name, _ in ANALYSIS_SECTIONS
            if name != "abstract"
            and len(sections.get(name, "")) > 400
        ]

        return len(body) >= 2

    def analysis_text(
        self,
        source,
        max_chars: int = 32000
    ) -> str:

        # Accepts raw text, a list of pages, or an already parsed section dict.

        sections = (
            source
            if isinstance(source, dict)
            else self.run(source)
        )

        parts = []

        for name, cap in ANALYSIS_SECTIONS:

            body = sections.get(name, "").strip()

            if not body:

                continue

            if len(body) > cap:

                body = body[:cap].rstrip() + "\n[section truncated]"

            parts.append(
                name.upper() + "\n" + body
            )

        extract = "\n\n".join(parts).strip()

        if not extract:

            extract = (
                "\n\n".join(sections.values())
                if isinstance(source, dict)
                else self._as_text(source)
            ).strip()

        if len(extract) > max_chars:

            extract = extract[:max_chars].rstrip() + "\n[truncated]"

        return extract
