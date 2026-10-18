import re
from app.models.contracts import Domain, RoutingDecision

TECH = {"cisco", "router", "network", "switch", "catalyst", "asr", "sd-wan", "vpn", "gcp", "cloud"}
SEC = {"sec", "10-k", "10q", "10-q", "filing", "risk factor", "revenue", "financial", "alphabet", "agilent", "cisco"}
CLINICAL = {"clinical", "patient", "diabetes", "covid", "heart", "knee", "trial", "diagnosis", "treatment"}
CSR = {"food security", "hunger", "nutrition", "fao", "sustainability", "csr"}

def _hits(text: str, words: set[str]) -> int:
    return sum(1 for w in words if w in text)

def route_question(question: str) -> RoutingDecision:
    text = question.lower()
    scores = {
        Domain.technology: _hits(text, TECH),
        Domain.sec: _hits(text, SEC),
        Domain.clinical: _hits(text, CLINICAL),
        Domain.csr: _hits(text, CSR),
    }
    domains = [d for d, score in scores.items() if score > 0]
    # Cisco alone is ambiguous: technology by default; add SEC only when filing/financial language is present.
    if "cisco" in text and scores[Domain.sec] == 1 and not any(x in text for x in ["sec", "filing", "risk", "revenue", "financial", "10-k", "10-q"]):
        domains = [d for d in domains if d != Domain.sec]
    if not domains:
        domains = [Domain.technology]
    missing = []
    needs = False
    if Domain.technology in domains and any(x in text for x in ["replace", "compatible", "failure", "broken", "part"]):
        model_match = re.search(r"\b(?:c8\d{3}|asr\s*\d{4}|isr\s*\d{4}|catalyst\s*\d{4})\b", text, re.I)
        if not model_match:
            missing.append("Exact product/model identifier")
            needs = True
    return RoutingDecision(
        detected_intent="enterprise consulting question",
        domains=domains,
        required_specialists=domains,
        extracted_entities=[x for x in ["Cisco" if "cisco" in text else None, "Alphabet" if "alphabet" in text else None, "Agilent" if "agilent" in text else None] if x],
        missing_information=missing,
        risk_level="high" if Domain.clinical in domains else "medium" if Domain.sec in domains else "low",
        rationale="Deterministic keyword/entity routing for the prototype.",
        needs_clarification=needs,
    )
