from typing import Optional

from pydantic import BaseModel


class CitationVerification(BaseModel):

    # "verified"   - DOI resolves and the metadata matches the cited paper
    # "unresolved" - no DOI, or the DOI is not registered
    # "mismatch"   - DOI resolves, but to a different paper
    # "unverified" - not checked, or the check could not complete
    #
    # Defaults to "unverified" on purpose: an unchecked citation must never
    # look checked.
    status: str = "unverified"

    doi_resolved: bool = False

    # Similarity between the cited title and the title behind the DOI, 0-1.
    title_match: float = 0.0

    resolved_title: str = ""

    resolved_year: int = 0

    # None when no claim was attached, so "not checked" stays distinct from
    # "checked and unsupported".
    claim_supported: Optional[bool] = None

    notes: str = ""
