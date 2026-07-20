from dotenv import load_dotenv
import os

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4")

TEMPERATURE = 0.2

MAX_TOKENS = 4096

PROJECT_NAME = "ResearchForge"