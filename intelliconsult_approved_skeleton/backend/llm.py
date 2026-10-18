
from ollama import Client

client = Client(
    host="http://localhost:11434",
    timeout=180
)

MODEL = "qwen3:1.7b"


def generate_answer(question, context="", domain="technology"):
    system_prompt = (
        f"You are an enterprise {domain} consulting agent. "
        "Give concise, practical recommendations. "
        "Do not invent technical specifications or source citations. "
        "If information is insufficient, clearly say so."
    )

    user_prompt = (
        f"Customer question:\n{question}\n\n"
        f"Available context:\n{context}\n\n"
        "Provide findings and recommended next actions."
    )

    response = client.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        think=False,
        options={
            "num_ctx": 4096,
            "num_predict": 250
        }
    )

    return response.message.content or ""