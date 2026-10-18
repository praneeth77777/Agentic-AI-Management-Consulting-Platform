from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, asdict
from itertools import combinations
from pathlib import Path
from typing import Iterable, Sequence
import json
import math

import pandas as pd


@dataclass(frozen=True)
class Rule:
    antecedent: tuple[str, ...]
    consequent: str
    support: float
    confidence: float
    lift: float
    antecedent_count: int
    joint_count: int
    score: float

    def to_dict(self) -> dict:
        d = asdict(self)
        d["antecedent"] = list(self.antecedent)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Rule":
        d = dict(d)
        d["antecedent"] = tuple(d["antecedent"])
        return cls(**d)


def load_baskets(csv_path: str | Path) -> list[tuple[str, ...]]:
    df = pd.read_csv(csv_path)
    item_cols = [c for c in df.columns if c.startswith("item_")]
    baskets: list[tuple[str, ...]] = []
    for row in df[item_cols].itertuples(index=False, name=None):
        items = tuple(dict.fromkeys(str(x).strip() for x in row if pd.notna(x) and str(x).strip()))
        if items:
            baskets.append(items)
    return baskets


def _itemset_counts(baskets: Iterable[Sequence[str]], max_size: int = 4) -> Counter[frozenset[str]]:
    counts: Counter[frozenset[str]] = Counter()
    for basket in baskets:
        unique = sorted(set(basket))
        for size in range(1, min(max_size, len(unique)) + 1):
            for combo in combinations(unique, size):
                counts[frozenset(combo)] += 1
    return counts


def mine_rules(
    baskets: Sequence[Sequence[str]],
    min_support: float = 0.008,
    min_confidence: float = 0.10,
    min_lift: float = 1.15,
    min_antecedent_count: int = 6,
    max_antecedent_size: int = 3,
) -> list[Rule]:
    """Mine single-item-consequent association rules.

    Rules are deliberately filtered for evidence strength. The score favors larger
    matching cart contexts but penalizes rules supported by very few transactions.
    """
    n = len(baskets)
    counts = _itemset_counts(baskets, max_size=max_antecedent_size + 1)
    single_counts = {next(iter(k)): v for k, v in counts.items() if len(k) == 1}
    rules: list[Rule] = []

    for itemset, joint_count in counts.items():
        size = len(itemset)
        if size < 2 or joint_count / n < min_support:
            continue
        for consequent in itemset:
            antecedent_set = itemset - {consequent}
            if len(antecedent_set) > max_antecedent_size:
                continue
            antecedent_count = counts.get(antecedent_set, 0)
            if antecedent_count < min_antecedent_count:
                continue
            confidence = joint_count / antecedent_count
            consequent_support = single_counts[consequent] / n
            lift = confidence / consequent_support if consequent_support else 0.0
            if confidence < min_confidence or lift < min_lift:
                continue

            # Evidence-aware ranking: confidence + lift, shrunk for tiny samples;
            # multi-item antecedents receive a modest specificity bonus.
            evidence = math.sqrt(joint_count / (joint_count + 5.0))
            specificity = 1.0 + 0.15 * (len(antecedent_set) - 1)
            score = confidence * math.log1p(lift) * evidence * specificity
            rules.append(
                Rule(
                    antecedent=tuple(sorted(antecedent_set)),
                    consequent=consequent,
                    support=joint_count / n,
                    confidence=confidence,
                    lift=lift,
                    antecedent_count=antecedent_count,
                    joint_count=joint_count,
                    score=score,
                )
            )
    rules.sort(key=lambda r: (r.score, r.confidence, r.lift, r.support), reverse=True)
    return rules


class MarketBasketRecommender:
    def __init__(self, rules: Sequence[Rule], products: Sequence[str]):
        self.rules = list(rules)
        self.products = sorted(set(products))

    def recommend(self, cart: Sequence[str], top_k: int = 5) -> list[dict]:
        cart_set = set(cart)
        if not cart_set:
            return []

        # For a multi-item cart, require evidence from at least two items in the
        # current combination. This prevents unrelated single-item rules from being
        # used as a fallback when the combination itself has no historical signal.
        min_context = 1 if len(cart_set) == 1 else 2
        matching = [
            rule for rule in self.rules
            if rule.consequent not in cart_set
            and len(rule.antecedent) >= min_context
            and set(rule.antecedent).issubset(cart_set)
        ]
        if not matching:
            return []

        # Use the most specific evidence available for this cart state.
        max_context = max(len(rule.antecedent) for rule in matching)
        matching = [rule for rule in matching if len(rule.antecedent) == max_context]

        by_item: dict[str, dict] = {}
        for rule in matching:
            context_bonus = 1.0 + 0.20 * max(0, len(rule.antecedent) - 1)
            adjusted = rule.score * context_bonus
            prev = by_item.get(rule.consequent)
            if prev is None or adjusted > prev["score"]:
                by_item[rule.consequent] = {
                    "item": rule.consequent,
                    "score": adjusted,
                    "confidence": rule.confidence,
                    "lift": rule.lift,
                    "support": rule.support,
                    "joint_count": rule.joint_count,
                    "matched_cart_items": list(rule.antecedent),
                    "reason": f"Observed with {', '.join(rule.antecedent)} in {rule.joint_count} training baskets",
                }

        return sorted(
            by_item.values(),
            key=lambda x: (x["score"], x["confidence"], x["lift"], x["support"]),
            reverse=True,
        )[:top_k]

    def save(self, path: str | Path) -> None:
        payload = {"products": self.products, "rules": [r.to_dict() for r in self.rules]}
        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "MarketBasketRecommender":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls([Rule.from_dict(x) for x in payload["rules"]], payload["products"])
