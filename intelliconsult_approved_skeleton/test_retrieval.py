
import os

os.environ["RETRIEVAL_MODE"] = "hybrid"

from backend.retrieval import hybrid_retrieve

question = (
    "What are the Cisco ASR 1000 router hardware "
    "capabilities, Ethernet interfaces, and redundancy features?"
)

results = hybrid_retrieve(
    question=question,
    domain="technology",
    limit=3
)

print(f"\nRetrieved {len(results)} passages\n")

for item in results:
    print("=" * 60)
    print("Evidence ID:", item.id)
    print("Source:", item.source)
    print("Page:", item.page)
    print("Retrieval:", item.retrieval)
    print("Text:", item.text[:500])
    print()
