import os
import requests

from tools.base_tool import BaseTool


class PDFDownloader(BaseTool):

    def __init__(self):

        super().__init__("PDF Downloader")

        os.makedirs(
            "data/papers",
            exist_ok=True
        )

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
            filename
        )

        if os.path.exists(file_path):

            return file_path

        response = requests.get(
            pdf_url,
            timeout=60
        )

        response.raise_for_status()

        with open(
            file_path,
            "wb"
        ) as file:

            file.write(
                response.content
            )

        return file_path