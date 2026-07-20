import re

from tools.base_tool import BaseTool


class SectionParser(BaseTool):

    def __init__(self):

        super().__init__(
            "Section Parser"
        )

    def run(
        self,
        text: str
    ):

        headings = [

            "abstract",

            "introduction",

            "related work",

            "background",

            "methodology",

            "methods",

            "experimental setup",

            "experiments",

            "results",

            "discussion",

            "conclusion",

            "references"
        ]

        pattern = re.compile(
            r"(?im)^(" +
            "|".join(
                re.escape(h)
                for h in headings
            ) +
            r")\s*$"
        )

        matches = list(
            pattern.finditer(text)
        )

        sections = {}

        for i, match in enumerate(matches):

            start = match.end()

            end = (
                matches[i + 1].start()
                if i + 1 < len(matches)
                else len(text)
            )

            name = (
                match.group(1)
                .lower()
            )

            sections[name] = text[
                start:end
            ].strip()

        return sections