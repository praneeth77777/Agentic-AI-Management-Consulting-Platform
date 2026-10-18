
from backend.verify import verify
from backend.contracts import Finding, Recommendation, Evidence

evidence = [
    Evidence(
        id="ev-1",
        domain="technology",
        source="cisco.pdf",
        page=3,
        text=(
            "ASR 1002-HX supports up to 100 Gbps "
            "and has eight 10 GE ports."
        ),
        retrieval="hybrid"
    ),
    Evidence(
        id="ev-2",
        domain="technology",
        source="cisco.pdf",
        page=7,
        text="Smart Licensing provides license flexibility.",
        retrieval="hybrid"
    )
]

findings = [
    Finding(
        domain="technology",
        summary="ASR 1002-HX supports 100 Gbps throughput.",
        evidence_ids=["ev-1"]
    )
]

recommendations = [
    Recommendation(
        domain="technology",
        action="Compare ASR 1002-HX throughput requirements",
        rationale="The device supports 100 Gbps throughput.",
        evidence_ids=["ev-2"],
        score=None
    )
]

issues = verify(findings, recommendations, evidence)

print("Verification issues:")
for issue in issues:
    print("-", issue)