
from ollama import Client

client = Client(
    host="http://localhost:11434",
    timeout=180
)

response = client.chat(
    model="qwen3:1.7b",
    messages=[
        {
            "role": "system",
            "content": (
                "You are an enterprise technology consultant. "
                "Provide short, clear answers. "
                "Do not invent technical specifications."
            )
        },
        {
            "role": "user",
            "content": (
                "A Cisco router keeps disconnecting. "
                "What are the first three things to investigate?"
            )
        }
    ],
    think=False,
    options={
        "num_ctx": 4096,
        "num_predict": 300
    }
)

print("AI Response:")
print(repr(response.message.content))

print("\nThinking:")
print(repr(response.message.thinking))