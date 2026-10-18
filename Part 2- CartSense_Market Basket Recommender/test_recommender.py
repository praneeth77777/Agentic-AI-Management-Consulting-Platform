from pathlib import Path
from recommender import MarketBasketRecommender

ROOT = Path(__file__).resolve().parent
model = MarketBasketRecommender.load(ROOT / "market_basket_model.json")


def test_empty_cart_has_no_recommendations():
    assert model.recommend([]) == []


def test_no_cart_item_is_recommended_again():
    item = model.products[0]
    assert all(x["item"] != item for x in model.recommend([item], top_k=10))


def test_results_are_ranked():
    for item in model.products:
        recs = model.recommend([item], top_k=10)
        scores = [x["score"] for x in recs]
        assert scores == sorted(scores, reverse=True)
