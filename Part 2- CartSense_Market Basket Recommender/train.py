from __future__ import annotations

from itertools import combinations
from pathlib import Path
import json
import random

import pandas as pd

from recommender import MarketBasketRecommender, load_baskets, mine_rules

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "CMPE256_Hackathon_market_basket_analysis_Release.csv"
MODEL = ROOT / "market_basket_model.json"
RULES_CSV = ROOT / "top_rules.csv"
METRICS = ROOT / "metrics.json"


def split_data(baskets, seed=42):
    x = list(baskets)
    random.Random(seed).shuffle(x)
    n = len(x)
    return x[: int(0.70*n)], x[int(0.70*n): int(0.85*n)], x[int(0.85*n):]


def evaluate(model, baskets, top_k=5):
    queries = hits = 0
    precision_sum = recall_sum = 0.0
    nonempty = 0
    recommended_items = set()

    for basket in baskets:
        b = list(basket)
        # Evaluate every cart state of size 1..min(3,n-1), independent of item order.
        for size in range(1, min(3, len(b)-1) + 1):
            for context in combinations(b, size):
                hidden = set(b) - set(context)
                recs = model.recommend(context, top_k=top_k)
                pred = [r["item"] for r in recs]
                queries += 1
                if pred:
                    nonempty += 1
                    recommended_items.update(pred)
                overlap = hidden.intersection(pred)
                if overlap:
                    hits += 1
                precision_sum += len(overlap) / len(pred) if pred else 0.0
                recall_sum += len(overlap) / len(hidden) if hidden else 0.0

    return {
        "queries": queries,
        f"hit_rate@{top_k}": hits / queries if queries else 0.0,
        f"precision@{top_k}": precision_sum / queries if queries else 0.0,
        f"recall@{top_k}": recall_sum / queries if queries else 0.0,
        "recommendation_availability": nonempty / queries if queries else 0.0,
        "catalog_coverage": len(recommended_items) / len(model.products) if model.products else 0.0,
    }


def main():
    baskets = load_baskets(DATA)
    train, val, test = split_data(baskets)
    products = sorted({x for b in train for x in b})

    # Small grid selected on validation hit rate, with precision as tie-breaker.
    configs = []
    for min_support in (0.006, 0.008, 0.010, 0.012):
        for min_confidence in (0.10, 0.12, 0.15):
            for min_lift in (1.10, 1.20, 1.30):
                rules = mine_rules(
                    train,
                    min_support=min_support,
                    min_confidence=min_confidence,
                    min_lift=min_lift,
                    min_antecedent_count=5,
                    max_antecedent_size=3,
                )
                model = MarketBasketRecommender(rules, products)
                m = evaluate(model, val, top_k=5)
                configs.append((m["hit_rate@5"], m["precision@5"], m["recommendation_availability"], min_support, min_confidence, min_lift))

    configs.sort(reverse=True)
    _, _, _, min_support, min_confidence, min_lift = configs[0]

    # Retrain on train+validation after threshold selection, then evaluate once on test.
    fit = train + val
    products = sorted({x for b in fit for x in b})
    rules = mine_rules(
        fit,
        min_support=min_support,
        min_confidence=min_confidence,
        min_lift=min_lift,
        min_antecedent_count=5,
        max_antecedent_size=3,
    )
    model = MarketBasketRecommender(rules, products)
    test_metrics = evaluate(model, test, top_k=5)
    test_metrics.update({
        "train_baskets": len(train),
        "validation_baskets": len(val),
        "test_baskets": len(test),
        "catalog_size": len(products),
        "rule_count": len(rules),
        "selected_min_support": min_support,
        "selected_min_confidence": min_confidence,
        "selected_min_lift": min_lift,
    })

    model.save(MODEL)
    METRICS.write_text(json.dumps(test_metrics, indent=2), encoding="utf-8")
    pd.DataFrame([r.to_dict() for r in rules]).head(100).to_csv(RULES_CSV, index=False)

    print(json.dumps(test_metrics, indent=2))
    print("\nTop 10 rules:")
    for r in rules[:10]:
        print(f"{r.antecedent} -> {r.consequent} | support={r.support:.3f} confidence={r.confidence:.3f} lift={r.lift:.2f} score={r.score:.3f}")


if __name__ == "__main__":
    main()
