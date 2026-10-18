
import os
from ollama import Client

from .contracts import Recommendation, Finding, Evidence

# Fallback actions for agents that still use mock data.
ACTIONS = {
    "technology": [
        "Collect model number and diagnostic logs",
        "Verify component compatibility before ordering"
    ],
    "clinical": [
        "Confirm laboratory specifications and throughput",
        "Validate the instrument against the official operating manual"
    ],
    "sec": [
        "Review disclosed risks and fiscal-year context",
        "Perform supplier due diligence"
    ],
    "csr": [
        "Define expected impact indicators",
        "Compare intervention feasibility against the budget"
    ],
}


def synthesize(
    findings: list[Finding],
    evidence: list[Evidence]
) -> list[Recommendation]:

    by_domain = {}

    for item in evidence:
        by_domain.setdefault(item.domain, []).append(item)

    output = []

    for finding in findings:
        domain = finding.domain
        domain_evidence = by_domain.get(domain, [])

        # Generate real recommendations only for Technology
        # when actual hybrid-retrieved evidence exists.
        real_evidence = [
            e for e in domain_evidence
            if e.retrieval == "hybrid"
        ]

        if domain == "technology" and real_evidence:
            output.extend(
                technology_recommendations(
                    finding,
                    real_evidence
                )
            )
        else:
            for action in ACTIONS[domain]:
                output.append(
                    Recommendation(
                        domain=domain,
                        action=action,
                        score=None,
                        rationale=(
                            "Illustrative action only; "
                            "not an evidence-backed recommendation."
                        ),
                        evidence_ids=[
                            e.id for e in domain_evidence
                        ]
                    )
                )

    return output



import json

def technology_recommendations(
    finding: Finding,
    evidence: list[Evidence]
) -> list[Recommendation]:

    client = Client(
        host="http://localhost:11434",
        timeout=180
    )

    evidence_by_id = {e.id: e for e in evidence}

    context = "\n\n".join(
        f"ID: {e.id}\n"
        f"Source: {e.source}\n"
        f"Page: {e.page}\n"
        f"Text: {e.text}"
        for e in evidence
    )
    
    recommendation_schema = {
        "type": "object",
        "properties": {
            "recommendations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string"},
                        "rationale": {"type": "string"},
                        "evidence_id": {"type": "string"}
                    },
                    "required": [
                        "action",
                        "rationale",
                        "evidence_id"
                    ]
                }
            }
        },
        "required": ["recommendations"]
    }


    response = client.chat(
        model=os.getenv("OLLAMA_MODEL", "qwen3:1.7b"),
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an enterprise technology consultant. "
                    "Generate exactly two practical recommendations. "
                    "Use only the provided document passages. "
                    "Each recommendation must have an action, "
                    "a rationale, and one supporting evidence_id. "
                    "The evidence_id must exactly match an ID "
                    "from the provided evidence. "
                    "Do not invent costs, product specifications, "
                    "or compatibility information. "
                    "Do not recommend a purchase without "
                    "customer-specific requirements."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Technology finding:\n{finding.summary}\n\n"
                    f"Available evidence:\n{context}"
                )
            }
        ],
        format=recommendation_schema,
        think=False,
        options={
            "num_ctx": 4096,
            "num_predict": 500,
            "temperature": 0
        }
    )

    print("\n========== RAW RECOMMENDATION RESPONSE ==========")
    print(response.message.content)
    print("=================================================\n")

    try:
        parsed = json.loads(response.message.content or "{}")
    except json.JSONDecodeError:
        parsed = {}

    print("Parsed recommendations:", parsed.get("recommendations"))
    print("Valid evidence IDs:", list(evidence_by_id.keys()))

    items = parsed.get("recommendations", [])

    recommendations = []

    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue

            action = item.get("action")
            rationale = item.get("rationale")
            evidence_id = item.get("evidence_id")

            if not all(
                isinstance(value, str) and value.strip()
                for value in (action, rationale, evidence_id)
            ):
                continue

            if evidence_id not in evidence_by_id:
                continue

            recommendations.append(
                Recommendation(
                    domain="technology",
                    action=action.strip(),
                    score=None,
                    rationale=rationale.strip(),
                    evidence_ids=[evidence_id]
                )
            )

            if len(recommendations) == 2:
                break

    if recommendations:
        return recommendations

    return [
        Recommendation(
            domain="technology",
            action=(
                "Confirm customer requirements before "
                "selecting a Cisco router"
            ),
            score=None,
            rationale=(
                "The model did not return recommendations "
                "with valid evidence references."
            ),
            evidence_ids=[]
        )
    ]