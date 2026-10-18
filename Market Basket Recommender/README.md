# CMPE 256 Hackathon — Market Basket Recommender

This project implements the retail track as a cart-aware association-rule recommender.

## What it does

- Loads the supplied 1,000-transaction retail dataset.
- Mines association rules with a single product as the consequent.
- Supports one-item and multi-item cart contexts.
- Ranks recommendations using confidence, lift, support/evidence, and context specificity.
- Returns **no recommendation** when no rule meets the evidence thresholds, rather than forcing an irrelevant suggestion.
- Tunes rule thresholds on a validation set and reports final metrics on a held-out test set.
- Exposes the recommender through FastAPI.
## Video presentation

https://youtu.be/We5Os7BAwBE

## Slide deck

A slide deck covering the pipeline, the five model families, the reported results, baseline comparisons, validation, and open research directions.

- [CartSense - Market Basket Recommender](https://docs.google.com/presentation/d/1RXjuwi-5arJ_t2qVXHH6ZltW7JahVG56w9TkgbEj44s/edit?usp=sharing)


## Files

- `recommender.py` — basket loader, rule miner, model, ranking logic.
- `train.py` — 70/15/15 split, validation tuning, test evaluation, artifact generation.
- `market_basket_model.json` — trained model.
- `top_rules.csv` — top association rules for analysis/presentation.
- `metrics.json` — held-out evaluation metrics.
- `app.py` — FastAPI service.
- `test_recommender.py` — basic behavioral tests.

## Train

```bash
python train.py
```

## Run API

```bash
uvicorn app:app --reload
```

Then use:

- `GET /health`
- `GET /products`
- `POST /recommend`

Example request body:

```json
{
  "cart": ["DSC WS4916 Smoke Detector (SKU: WS4916)"],
  "top_k": 5
}
```

Each recommendation includes confidence, lift, support, matched cart items, and a short explanation so the result is presentation-friendly and auditable.

## Run the interactive demo

```bash
py -m uvicorn app:app --reload
```

Open `http://127.0.0.1:8000/` in a browser. The same FastAPI process serves both the checkout-style UI and recommendation endpoints.
