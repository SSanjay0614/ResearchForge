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
