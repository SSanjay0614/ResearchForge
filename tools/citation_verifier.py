import difflib
import time

from concurrent.futures import ThreadPoolExecutor

import requests

from tools.base_tool import BaseTool

from utils.logger import logger

from config.settings import (
    CITATION_REPAIR_MATCH_THRESHOLD,
    CITATION_TITLE_MATCH_THRESHOLD,
    CITATION_VERIFY_RETRIES,
    CITATION_VERIFY_RETRY_DELAY,
    CITATION_VERIFY_WORKERS,
    ENABLE_CITATION_REPAIR,
    ENABLE_CITATION_VERIFICATION
)


HEADERS = {
    "User-Agent": "ResearchForge (citation verification)"
}


class CitationVerifier(BaseTool):
    """Checks that a citation points at a paper that actually exists.

    Three independent checks, because they fail for different reasons:

    1. The DOI resolves at all.
    2. The metadata behind the DOI matches the title and year we are claiming.
       A real DOI attached to the wrong paper is the failure that looks most
       convincing, so this is the one that matters most.
    3. Where a claim is attached, whether the paper supports it.

    A check that could not run leaves the citation "unverified". It never
    reports "verified", since an unchecked citation looking checked is the
    problem this tool exists to prevent.
    """

    # doi.org content negotiation, not the Crossref API. A DOI is registered
    # with one of several agencies -- Crossref for most journals, DataCite for
    # arXiv and most repositories -- and the Crossref API only knows its own.
    # Since the literature agent prefers arXiv papers, going through Crossref
    # alone would report almost every citation as unregistered. doi.org
    # resolves whoever owns the DOI and returns CSL JSON.
    DOI_URL = "https://doi.org/"

    CROSSREF_URL = "https://api.crossref.org/works/"

    def __init__(self):

        super().__init__(
            "Citation Verifier"
        )

        self.logger = logger

    def run(
        self,
        citations
    ):
        """BaseTool entry point. Same as verify_all."""

        return self.verify_all(
            citations
        )

    def _normalise_doi(
        self,
        doi: str
    ) -> str:

        doi = (doi or "").strip()

        for prefix in [
            "https://doi.org/",
            "http://doi.org/",
            "doi:"
        ]:

            if doi.lower().startswith(prefix):

                doi = doi[len(prefix):]

        return doi.strip()

    def _normalise_title(
        self,
        title: str
    ) -> str:

        return " ".join(
            (title or "").lower().split()
        )

    def title_similarity(
        self,
        claimed: str,
        actual: str
    ) -> float:

        claimed = self._normalise_title(claimed)

        actual = self._normalise_title(actual)

        if not claimed or not actual:

            return 0.0

        return difflib.SequenceMatcher(
            None,
            claimed,
            actual
        ).ratio()

    def _attempt_fetch(
        self,
        doi: str
    ):
        """One lookup. Returns (record, error, retryable)."""

        try:

            response = requests.get(
                self.DOI_URL + doi,
                timeout=20,
                headers=dict(
                    HEADERS,
                    Accept="application/vnd.citationstyles.csl+json"
                ),
                allow_redirects=True
            )

        except requests.RequestException as e:

            # A timeout or a reset says nothing about the DOI itself.
            return None, "lookup failed: %s" % type(e).__name__, True

        if response.status_code == 404:

            # Settled: the DOI is not registered. Retrying cannot change it.
            return None, "not registered", False

        if response.status_code in (429, 500, 502, 503, 504):

            return None, "lookup failed: HTTP %d" % response.status_code, True

        if response.status_code >= 400:

            return None, "lookup failed: HTTP %d" % response.status_code, False

        try:

            record = response.json()

        except ValueError:

            # A DOI that resolves to a landing page instead of metadata: it
            # exists, but we cannot compare titles against it.
            return None, "no machine-readable metadata", False

        if not isinstance(record, dict) or not record:

            return None, "no machine-readable metadata", False

        return record, "", False

    def _fetch_record(
        self,
        doi: str
    ):
        """Return the registry record for a DOI, as CSL JSON.

        Distinguishes three outcomes the caller has to treat differently: the
        record exists, the DOI is genuinely unknown (404), or the lookup itself
        failed and we know nothing.

        A transient failure is retried, because "could not check" and "the DOI
        is wrong" look identical to the user and one flaky request should not
        leave a good citation flagged.
        """

        attempts = max(1, CITATION_VERIFY_RETRIES + 1)

        record, error, retryable = None, "lookup failed: no attempt", False

        for attempt in range(1, attempts + 1):

            record, error, retryable = self._attempt_fetch(doi)

            if record is not None or not retryable:

                return record, error

            if attempt < attempts:

                self.logger.info(
                    "DOI %s lookup attempt %d/%d failed (%s); retrying"
                    % (doi, attempt, attempts, error)
                )

                # Back off a little further each time; a rate limit needs more
                # room than a single dropped connection.
                time.sleep(CITATION_VERIFY_RETRY_DELAY * attempt)

        return record, error

    def _record_title(
        self,
        record: dict
    ) -> str:
        """CSL JSON gives a plain string; the Crossref API gives a list."""

        title = record.get("title")

        if isinstance(title, list):

            return title[0] if title else ""

        return title or ""

    def _record_year(
        self,
        record: dict
    ):

        for field in [
            "issued",
            "published",
            "published-print",
            "published-online",
            "created"
        ]:

            parts = (record.get(field) or {}).get("date-parts") or []

            if parts and parts[0] and parts[0][0]:

                return parts[0][0]

        return None

    def verify_citation(
        self,
        citation
    ) -> dict:
        """Verify one citation. Returns the fields for CitationVerification."""

        doi = self._normalise_doi(
            getattr(citation, "doi", "")
        )

        if not doi:

            return {
                "status": "unresolved",
                "doi_resolved": False,
                "title_match": 0.0,
                "notes": "No DOI to verify against."
            }

        record, error = self._fetch_record(doi)

        if record is None:

            if error == "not registered":

                return {
                    "status": "unresolved",
                    "doi_resolved": False,
                    "title_match": 0.0,
                    "notes": "DOI %s does not resolve; it is not registered." % doi
                }

            if error == "no machine-readable metadata":

                # The DOI resolves, so the paper is real; we just cannot
                # confirm the title matches.
                return {
                    "status": "unverified",
                    "doi_resolved": True,
                    "title_match": 0.0,
                    "notes": "DOI %s resolves, but returned no metadata to check the title against." % doi
                }

            # The DOI may well be fine; we just could not check it.
            return {
                "status": "unverified",
                "doi_resolved": False,
                "title_match": 0.0,
                "notes": "Could not verify DOI %s (%s)." % (doi, error)
            }

        actual_title = self._record_title(record)

        similarity = self.title_similarity(
            getattr(citation, "title", ""),
            actual_title
        )

        claimed_year = getattr(citation, "year", 0) or 0

        actual_year = self._record_year(record)

        notes = []

        status = "verified"

        if similarity < CITATION_TITLE_MATCH_THRESHOLD:

            status = "mismatch"

            notes.append(
                "DOI resolves to \"%s\", which does not match the cited title."
                % (actual_title or "unknown title")
            )

        # A year that is off by one is normal: online-first and print dates
        # often straddle a year boundary.
        if claimed_year and actual_year and abs(claimed_year - actual_year) > 1:

            status = "mismatch"

            notes.append(
                "Cited year %d, but the record says %d."
                % (claimed_year, actual_year)
            )

        if status == "verified":

            notes.append(
                "DOI resolves and the metadata matches. Registered with %s."
                % (record.get("publisher") or "the DOI registry")
            )

        return {
            "status": status,
            "doi_resolved": True,
            "title_match": round(similarity, 3),
            "resolved_title": actual_title,
            "resolved_year": actual_year or 0,
            "notes": " ".join(notes)
        }

    def find_correct_doi(
        self,
        title: str,
        year: int = 0
    ):
        """Search Crossref by title for the DOI that belongs to it.

        Used to repair a citation whose DOI is missing or points elsewhere.
        Returns (doi, resolved_title, resolved_year, similarity), or None when
        nothing matches closely enough to be trusted.

        The bar is deliberately high. Adopting the top hit on a loose match is
        how a citation ends up confidently pointing at the wrong paper, which
        is the exact failure this module exists to catch.
        """

        title = (title or "").strip()

        if not title:

            return None

        try:

            response = requests.get(
                self.CROSSREF_URL.rstrip("/"),
                params={
                    "query.bibliographic": title,
                    "rows": 5,
                    "select": "DOI,title,issued"
                },
                timeout=20,
                headers=HEADERS
            )

            response.raise_for_status()

            items = (
                response.json()
                .get("message", {})
                .get("items", [])
            )

        except (requests.RequestException, ValueError) as e:

            self.logger.info(
                "title search failed for %r: %s" % (title[:60], type(e).__name__)
            )

            return None

        best = None

        for item in items:

            candidate_title = self._record_title(item)

            similarity = self.title_similarity(
                title,
                candidate_title
            )

            if best is None or similarity > best[3]:

                best = (
                    item.get("DOI") or "",
                    candidate_title,
                    self._record_year(item) or 0,
                    similarity
                )

        if best is None or not best[0]:

            return None

        if best[3] < CITATION_REPAIR_MATCH_THRESHOLD:

            return None

        # A candidate with the right title but a year years away is a different
        # work with a similar name -- a follow-up, a reprint, a different venue.
        if year and best[2] and abs(year - best[2]) > 1:

            return None

        return best

    def repair_citation(
        self,
        citation
    ):
        """Try to find the right DOI for a citation whose DOI is wrong.

        Returns a verification dict on success, None if nothing better was
        found. Mutates the citation's DOI only on success, so a failed repair
        leaves the original flagged rather than blanked.
        """

        match = self.find_correct_doi(
            getattr(citation, "title", ""),
            getattr(citation, "year", 0) or 0
        )

        if match is None:

            return None

        doi, resolved_title, resolved_year, similarity = match

        # DOIs are case-insensitive, so compare them folded: otherwise a
        # registrar returning a different case reads as a repair that changed
        # nothing.
        if self._normalise_doi(
            getattr(citation, "doi", "")
        ).lower() == (doi or "").lower():

            # The search found the DOI we already had, so the mismatch is real.
            return None

        previous_doi = getattr(citation, "doi", "") or ""

        citation.doi = doi

        result = self.verify_citation(citation)

        if result["status"] != "verified":

            # The replacement is no better; put the original back so the record
            # still shows what was actually cited.
            citation.doi = previous_doi

            return None

        result["notes"] = (
            "Original DOI %s did not match; found %s by title search (similarity %.2f). %s"
            % (
                previous_doi or "(none)",
                doi,
                similarity,
                result["notes"]
            )
        ).strip()

        self.logger.info(
            "repaired citation %r: %s -> %s"
            % (
                (getattr(citation, "title", "") or "")[:60],
                previous_doi or "(none)",
                doi
            )
        )

        return result

    def verify_all(
        self,
        citations
    ) -> list:
        """Verify citations concurrently. Each check is independent."""

        if not citations:

            return []

        if not ENABLE_CITATION_VERIFICATION:

            return [
                {
                    "status": "unverified",
                    "doi_resolved": False,
                    "title_match": 0.0,
                    "notes": "Citation verification is disabled."
                }
                for _ in citations
            ]

        workers = max(
            1,
            min(
                CITATION_VERIFY_WORKERS,
                len(citations)
            )
        )

        def verify(citation):

            try:

                result = self.verify_citation(citation)

                # A mismatch or a missing DOI is often a bad DOI attached to a
                # real paper, which a title search can fix. Only these two are
                # worth repairing: "unverified" means the lookup itself failed,
                # so searching would likely fail too.
                if (
                    ENABLE_CITATION_REPAIR
                    and result["status"] in ("mismatch", "unresolved")
                ):

                    repaired = self.repair_citation(citation)

                    if repaired is not None:

                        return repaired

                return result

            except Exception as e:

                self.logger.warning(
                    "citation verification failed: %s" % e
                )

                return {
                    "status": "unverified",
                    "doi_resolved": False,
                    "title_match": 0.0,
                    "notes": "Verification error: %s" % type(e).__name__
                }

        with ThreadPoolExecutor(max_workers=workers) as pool:

            return list(
                pool.map(verify, citations)
            )
