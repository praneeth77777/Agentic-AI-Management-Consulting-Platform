from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from recommender import MarketBasketRecommender

ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "market_basket_model.json"

app = FastAPI(
    title="CMPE 256 Market Basket Recommender",
    version="1.0.0",
    description="Cart-aware association-rule recommender for the hackathon retail dataset.",
)
model = MarketBasketRecommender.load(MODEL_PATH)


class RecommendRequest(BaseModel):
    cart: List[str] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1, le=20)


@app.get("/", include_in_schema=False)
def demo_ui():
    return FileResponse(ROOT / "index.html")


@app.get("/health")
def health():
    return {"status": "ok", "products": len(model.products), "rules": len(model.rules)}


@app.get("/products")
def products():
    return {"products": model.products}


@app.post("/recommend")
def recommend(req: RecommendRequest):
    unknown = sorted(set(req.cart) - set(model.products))
    if unknown:
        raise HTTPException(status_code=400, detail={"unknown_products": unknown})
    recs = model.recommend(req.cart, top_k=req.top_k)
    return {
        "cart": req.cart,
        "recommendations": recs,
        "message": "No sufficiently strong historical pattern found." if not recs else None,
    }
