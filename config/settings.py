from dotenv import load_dotenv
import os


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:31b-cloud")

# Only needed when talking to Ollama Cloud directly (OLLAMA_BASE_URL set to
# https://ollama.com), which is the case for a hosted deployment where there
# is no local ollama daemon to sign the request. Locally this stays empty and
# the daemon authenticates with the key pair from `ollama signin`.
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")

# "ollama" or "gemini". "ollama" covers both a local daemon and Ollama Cloud,
# which is selected by the model tag (e.g. gemma4:31b-cloud) rather than by a
# separate backend.
LLM_BACKEND = os.getenv("LLM_BACKEND", "ollama").strip().lower()

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemma-4-31b-it")

TEMPERATURE = 0.2

MAX_TOKENS = 4096

# Local Ollama models default to a 4096-token context and silently drop
# anything past it, which quietly breaks full-paper analysis. 16384 holds a
# section extract plus the prompt and the reply. Raising it further makes a
# local model spill out of VRAM onto the CPU. Cloud models manage context
# server-side and ignore this.
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "16384"))

PROJECT_NAME = "ResearchForge"

# ---------------------------------------------------------------
# Literature pipeline
# ---------------------------------------------------------------

# Characters of section-extracted paper text sent to the analyzer.
# ~32k chars is roughly 8k tokens.
FULL_TEXT_MAX_CHARS = int(os.getenv("FULL_TEXT_MAX_CHARS", "32000"))

# Set to 0 to go back to abstract-only analysis.
ENABLE_FULL_TEXT_ANALYSIS = os.getenv("ENABLE_FULL_TEXT_ANALYSIS", "1") != "0"

# Relevance checks are independent, so they are issued concurrently.
RELEVANCE_WORKERS = int(os.getenv("RELEVANCE_WORKERS", "5"))

# How many relevant papers the search is aiming for, and the ceiling on how
# many get analyzed. Every relevant paper is analyzed, so these are normally
# the same number: a paper judged relevant but left unanalyzed is the confusing
# case ("found 13, analyzed 3").
TARGET_RELEVANT_PAPERS = int(os.getenv("TARGET_RELEVANT_PAPERS", "10"))

MAX_ANALYZED_PAPERS = int(
    os.getenv("MAX_ANALYZED_PAPERS", str(TARGET_RELEVANT_PAPERS))
)

# Papers requested per source per iteration. Both sources are queried, so the
# ceiling per iteration is roughly twice this before deduplication.
MAX_RETRIEVED_PAPERS = int(os.getenv("MAX_RETRIEVED_PAPERS", "10"))

# Reformulate the query and search again while the target is unmet.
MAX_SEARCH_ITERATIONS = int(os.getenv("MAX_SEARCH_ITERATIONS", "4"))

# Discard papers judged off-topic instead of keeping them flagged. Keeping them
# makes a wrong relevance verdict visible and recoverable; dropping them gives
# a clean list of only what matters.
DROP_IRRELEVANT_PAPERS = os.getenv("DROP_IRRELEVANT_PAPERS", "1") != "0"

# ---------------------------------------------------------------
# Citation verification
# ---------------------------------------------------------------

# Check every citation's DOI against Crossref before it is presented.
# Set to 0 to skip the lookups; citations are then marked "unverified"
# rather than being silently treated as correct.
ENABLE_CITATION_VERIFICATION = os.getenv(
    "ENABLE_CITATION_VERIFICATION",
    "1"
) != "0"

# Crossref lookups are independent, so they are issued concurrently.
CITATION_VERIFY_WORKERS = int(os.getenv("CITATION_VERIFY_WORKERS", "5"))

# How closely a Crossref title has to match the cited title to count as the
# same paper. Titles differ in punctuation, subtitles and capitalisation, so
# this compares loosely; 0.75 separates those from a DOI pointing at an
# entirely different paper.
CITATION_TITLE_MATCH_THRESHOLD = float(
    os.getenv("CITATION_TITLE_MATCH_THRESHOLD", "0.75")
)

# Retries for a DOI lookup that failed for a transient reason -- a timeout, a
# connection reset, a 5xx. A 404 is not retried: the DOI is genuinely
# unregistered and asking again will not change that. Without this, one flaky
# request leaves a perfectly good citation marked "unverified".
CITATION_VERIFY_RETRIES = int(os.getenv("CITATION_VERIFY_RETRIES", "2"))

CITATION_VERIFY_RETRY_DELAY = float(
    os.getenv("CITATION_VERIFY_RETRY_DELAY", "1.0")
)

# When a citation's DOI resolves to the wrong paper, or has no DOI at all,
# search by title for the correct one and adopt it if it matches well. Set to 0
# to leave such citations flagged without attempting a repair.
ENABLE_CITATION_REPAIR = os.getenv("ENABLE_CITATION_REPAIR", "1") != "0"

# A replacement DOI found by title search is only adopted above this
# similarity. Deliberately stricter than the verification threshold: accepting
# the top search hit on a loose match is what produces a confident citation
# pointing at an unrelated paper.
CITATION_REPAIR_MATCH_THRESHOLD = float(
    os.getenv("CITATION_REPAIR_MATCH_THRESHOLD", "0.90")
)
