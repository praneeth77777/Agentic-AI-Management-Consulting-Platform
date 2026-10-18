from .contracts import Recommendation, Finding, Evidence
# Demonstration only: these are possible next actions, NOT product recommendations.
ACTIONS={
 'technology':['Collect model number and diagnostic logs','Verify component compatibility before ordering'],
 'clinical':['Confirm laboratory specifications and throughput','Validate the instrument against the official operating manual'],
 'sec':['Review disclosed risks and fiscal-year context','Perform supplier due diligence'],
 'csr':['Define expected impact indicators','Compare intervention feasibility against the budget'],
}
def synthesize(findings: list[Finding], evidence: list[Evidence]) -> list[Recommendation]:
    by_domain={}
    for item in evidence:by_domain.setdefault(item.domain,[]).append(item.id)
    output=[]
    for f in findings:
        for action in ACTIONS[f.domain]:
            output.append(Recommendation(domain=f.domain,action=action,
                score=None, rationale='Illustrative action only; no evidence-backed scoring until real candidate data is available.',
                evidence_ids=by_domain.get(f.domain,[])))
    return output
