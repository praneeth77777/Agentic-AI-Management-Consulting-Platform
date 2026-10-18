from pathlib import Path
from recommender import MarketBasketRecommender

ROOT = Path(__file__).resolve().parent
model = MarketBasketRecommender.load(ROOT / 'market_basket_model.json')

examples = [
    ['Honeywell 5800CO Carbon Monoxide Detector (SKU: 5800CO)'],
    [
        'Axis M3046-V Network Camera (SKU: 0806-001)',
        'Axis P3225-LVE Network Camera (SKU: 0935-001)',
    ],
]

for cart in examples:
    print('\nCART')
    for item in cart:
        print(' -', item)
    recs = model.recommend(cart, top_k=5)
    if not recs:
        print('No sufficiently strong historical pattern found.')
    else:
        print('RECOMMENDATIONS')
        for i, r in enumerate(recs, 1):
            print(f"{i}. {r['item']}")
            print(f"   confidence={r['confidence']:.3f}, lift={r['lift']:.2f}, support={r['support']:.3f}")
            print('   ', r['reason'])
