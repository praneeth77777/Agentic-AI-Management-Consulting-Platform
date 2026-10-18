import os
from .contracts import Domain, Finding, Evidence
PROMPTS={
 'technology':'You are a technology consultant. Do not guess model numbers or compatibility.',
 'clinical':'You advise on laboratory equipment, not patient diagnosis or treatment.',
 'sec':'You analyze SEC disclosures; distinguish filings from your interpretations.',
 'csr':'You analyze sustainability and food-security programs; do not invent impact numbers.',
}
def specialist(question: str, domain: Domain, evidence: list[Evidence]) -> Finding:
    ids=[e.id for e in evidence]
    if os.getenv('AGENT_MODE','mock')!='ollama':
        return Finding(domain=domain,summary=f'[MOCK {domain.upper()}] Review the retrieved evidence and request missing requirements before recommending a purchase.',evidence_ids=ids)
    from ollama import chat
    context='\n'.join(f'[{e.id}] {e.text[:950]}' for e in evidence)
    response=chat(model=os.getenv('OLLAMA_MODEL','qwen3:1.7b'),
      messages=[{'role':'system','content':PROMPTS[domain]+' Use only the supplied evidence; say if insufficient. Keep your reply under 90 words.'},
                {'role':'user','content':f'Customer: {question}\nEvidence:\n{context}'}],
      options={'num_ctx':4096,'num_predict':160})
    return Finding(domain=domain,summary=response.message.content or '(No response)',evidence_ids=ids)
