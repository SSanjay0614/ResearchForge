import json
import re


def parse_json(response: str) -> dict:

    response = response.strip()

    response = response.replace("```json", "")

    response = response.replace("```", "")

    response = response.strip()

    try:
        return json.loads(response)

    except json.JSONDecodeError:

        match = re.search(
            r"\{.*\}",
            response,
            re.DOTALL
        )

        if match:

            return json.loads(
                match.group()
            )

        raise ValueError(
            "Could not parse LLM response as JSON."
        )