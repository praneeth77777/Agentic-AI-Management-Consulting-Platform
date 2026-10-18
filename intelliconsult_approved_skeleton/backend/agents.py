
import os
from ollama import Client
from .contracts import Domain, Finding, Evidence

PROMPTS = {
    "technology": (
        "You are a technology consultant. "
        "Do not guess model numbers or compatibility."
    ),
    "clinical": (
        "You advise on laboratory equipment, "
        "not patient diagnosis or treatment."
    ),
    "sec": (
        "You analyze SEC disclosures. "
        "Distinguish filings from your interpretations."
    ),
    "csr": (
        "You analyze sustainability and food-security programs. "
        "Do not invent impact numbers."
    ),
}


def specialist(
    question: str,
    domain: Domain,
    evidence: list[Evidence]
) -> Finding:

    ids = [e.id for e in evidence]

    # Keep other agents in mock mode for now.
    agent_mode = os.getenv("AGENT_MODE", "mock")

    if agent_mode != "ollama" or domain != "technology":
        return Finding(
            domain=domain,
            summary=(
                f"[MOCK {domain.upper()}] "
                "Review the retrieved evidence and request "
                "missing requirements before recommending a purchase."
            ),
            evidence_ids=ids
        )

    # Do not generate a document-grounded answer
    # when there is no retrieved evidence.
    if not evidence:
        return Finding(
            domain=domain,
            summary=(
                "Insufficient retrieved evidence to make "
                "a reliable technology recommendation."
            ),
            evidence_ids=[]
        )

    context = "\n".join(
        f"[{e.id}] {e.text[:950]}"
        for e in evidence
    )

    client = Client(
        host="http://localhost:11434",
        timeout=180
    )

    response = client.chat(
        model=os.getenv("OLLAMA_MODEL", "qwen3:1.7b"),
        messages=[
            {
                "role": "system",
                "content": (
                    PROMPTS[domain]
                    + " Use only the supplied evidence. "
                    "If the evidence is insufficient, say so. "
                    "Do not invent document citations. "
                    "Keep your response under 90 words."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Customer question:\n{question}\n\n"
                    f"Retrieved evidence:\n{context}"
                )
            }
        ],
        think=False,
        options={
            "num_ctx": 4096,
            "num_predict": 250
        }
    )

    answer = response.message.content or (
        "The local model returned no response."
    )

    return Finding(
        domain=domain,
        summary=answer,
        evidence_ids=ids
    )