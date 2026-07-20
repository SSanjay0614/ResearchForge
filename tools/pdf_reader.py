import fitz
import re

from tools.base_tool import BaseTool


class PDFReader(BaseTool):

    def __init__(self):

        super().__init__(
            "PDF Reader"
        )

    def run(
        self,
        pdf_path: str
    ) -> list[str]:

        document = fitz.open(
            pdf_path
        )

        pages = []

        for page in document:

            pages.append(
                page.get_text()
            )

        document.close()

        return pages
    
    def extract_abstract(
        self,
        pdf_path: str
    ) -> str:

        pages = self.run(
            pdf_path
        )

        text = "\n".join(pages)

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        start = re.search(
            r"abstract[:\s]*",
            text,
            re.IGNORECASE
        )

        if not start:
            return ""

        start = start.end()

        end = re.search(
            r"\b(introduction|1\.)\b",
            text[start:],
            re.IGNORECASE
        )

        if end:
            return text[
                start:
                start + end.start()
            ].strip()

        return text[start:start + 3000].strip()