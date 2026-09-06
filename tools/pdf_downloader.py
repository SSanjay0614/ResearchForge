import os
import re

import requests

from tools.base_tool import BaseTool


# Publishers commonly return their landing page (200 + text/html) instead of
# the PDF, and some block non-browser clients outright.

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/pdf,*/*",
}


class NotAPDFError(Exception):
    """The server answered, but what came back was not a PDF."""


class PDFDownloader(BaseTool):

    def __init__(self):

        super().__init__("PDF Downloader")

        os.makedirs(
            "data/papers",
            exist_ok=True
        )

    def _safe_name(
        self,
        filename: str
    ) -> str:

        name = os.path.basename(filename or "").strip()

        name = re.sub(r"[^A-Za-z0-9._-]", "_", name)

        if not name or name in (".", ".."):

            name = "paper.pdf"

        if not name.lower().endswith(".pdf"):

            name += ".pdf"

        return name[:120]

    def run(
        self,
        pdf_url: str,
        filename: str
    ) -> str:

        if not pdf_url:

            raise ValueError(
                "Paper does not have an accessible PDF."
            )

        file_path = os.path.join(
            "data",
            "papers",
            self._safe_name(filename)
        )

        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:

            return file_path

        response = requests.get(
            pdf_url,
            headers=HEADERS,
            timeout=60,
            allow_redirects=True
        )

        response.raise_for_status()

        content = response.content

        content_type = response.headers.get(
            "Content-Type",
            ""
        ).lower()

        # The magic bytes are the reliable check. Content-Type only tells us
        # what the server claims, and a landing page claiming text/html is a
        # useful early signal for the error message.

        if not content.lstrip()[:5].startswith(b"%PDF"):

            raise NotAPDFError(
                "%s returned %s, not a PDF (%d bytes)."
                % (pdf_url, content_type or "an unknown content type", len(content))
            )

        with open(file_path, "wb") as file:

            file.write(content)

        return file_path
