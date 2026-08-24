from google import genai

from config.settings import GEMINI_API_KEY

client = genai.Client(
    api_key=GEMINI_API_KEY
)

response = client.models.generate_content(
    model="gemma-4-31b-it",
    contents="Say hello in one sentence.",
    config={
        "max_output_tokens": 100
    }
)

print(response.text)