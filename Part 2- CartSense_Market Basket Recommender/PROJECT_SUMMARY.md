# Project status

## Completed

1. Parsed the supplied retail dataset: 1,000 baskets and 40 products.
2. Implemented association-rule mining without an external Apriori dependency.
3. Added support, confidence, lift, antecedent-count, evidence, and specificity logic.
4. Added cart-aware recommendation behavior for one-item and multi-item carts.
5. Added a conservative no-recommendation path for weak combinations.
6. Added a 70/15/15 train/validation/test workflow and validation-based threshold tuning.
7. Evaluated the final model on a held-out test set.
8. Exported the trained JSON model and top-rule CSV.
9. Added a FastAPI microservice with health, catalog, and recommendation endpoints.
10. Added and passed behavioral tests.
11. Added a checkout-style browser demo served from FastAPI at `/`.
12. Added a hackathon report and a seven-slide presentation deck.

## Held-out metrics

- Hit rate@5: 7.84%
- Precision@5: 1.95%
- Recall@5: 2.97%
- Recommendation availability: 28.28%
- Catalog coverage among emitted recommendations: 100%
- Learned rules: 211

## Demo

```bash
uvicorn app:app --reload
```

Open `http://127.0.0.1:8000/`.
