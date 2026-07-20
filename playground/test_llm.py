from llm import ollama_provider

llm = ollama_provider.get_llm()

response = llm.invoke("Say hello in one sentence.")

print(response.content)