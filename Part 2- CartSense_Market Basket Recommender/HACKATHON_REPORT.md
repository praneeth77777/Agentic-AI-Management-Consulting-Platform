# CMPE 256 Hackathon — CartSense Market Basket Recommender

## Executive summary

CartSense is a cart-aware product recommender for the supplied electronic-security retail dataset. It mines association rules from historical baskets, ranks candidate next products using support, confidence, lift, evidence size, and cart-context specificity, and deliberately suppresses recommendations when the current basket does not have enough historical evidence.

The final system includes a trained JSON model, evaluation workflow, FastAPI service, and an interactive checkout-style web demo served from the same application.

## Dataset

- 1,000 historical baskets
- 40 unique products
- 2–5 items per basket
- 70/15/15 train/validation/test split

## Method

The training pipeline counts itemsets and creates single-item-consequent association rules. Candidate rules must pass minimum thresholds selected on the validation set:

- minimum support: 0.008
- minimum confidence: 0.10
- minimum lift: 1.20
- minimum antecedent count: evidence threshold inside the miner

The ranking score combines confidence and lift with a small-sample evidence shrinkage term and a specificity bonus for larger antecedents.

### Cart-awareness rule

For a one-item cart, a one-item antecedent can generate recommendations. For a cart containing two or more items, recommendations must be backed by a rule that matches at least two products already in the cart. The ranker then keeps the most specific available context.

This prevents an unrelated single-item association from being used as a fallback when the actual multi-product combination has no historical signal.

## API and demo

The FastAPI application exposes:

- `GET /` — interactive checkout demo
- `GET /health` — model status
- `GET /products` — product catalog
- `POST /recommend` — ranked cart recommendations

Run with:

```bash
uvicorn app:app --reload
```

Then open `http://127.0.0.1:8000/`.

## Held-out results

| Metric | Result |
|---|---:|
| Hit rate@5 | 7.84% |
| Precision@5 | 1.95% |
| Recall@5 | 2.97% |
| Recommendation availability | 28.28% |
| Catalog coverage among emitted recommendations | 100% |
| Learned rules | 211 |

The relatively modest hit/precision values reflect the weak co-purchase structure in the supplied synthetic-style catalog. The selective 28.3% recommendation availability is intentional: the system prioritizes evidence-backed suggestions over always returning an answer.

## Example rule

A strong learned rule is:

**Honeywell 5800CO Carbon Monoxide Detector → DSC WS4916 Smoke Detector**

- confidence: 19.7%
- lift: 2.17×
- observed joint count: 13 training baskets

The live interface displays these evidence signals next to each suggestion so the recommendation is explainable during the demo.

## Requirement coverage

The solution meets the main retail-track requirements:

- Recommendations begin after the first cart item.
- Ranking recomputes after cart additions or removals.
- Recommendations are ranked.
- Multi-item cart combinations use combination-aware evidence.
- Weak combinations return no recommendation rather than unrelated products.
- The recommender is exposed as a FastAPI microservice suitable for checkout integration.

## Limitations and next improvements

A production system would benefit from substantially more transaction history, timestamps, quantities, customer/session context, price and inventory features, and offline/online A/B testing. With a larger dataset, the model could also compare association rules against sequence models, matrix-factorization approaches, and learning-to-rank methods.
