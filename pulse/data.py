"""Data layer: a realistic synthetic generator + real-CSV adapters.

A record is a plain dict:
    {brand, text, date (YYYY-MM-DD), rating (1-5 or None), product, platform}

The synthetic generator is *seeded* so findings are reproducible, and it deliberately
bakes in structure (a rising "quiet luxury" theme, one house with a price/service
problem) so the analysis surfaces a clear, defensible narrative on demo data.

For real findings, drop in a Kaggle CSV and use load_csv(...). The Sephora reviews
dataset is the natural fit — Sephora is an LVMH maison.
"""
from __future__ import annotations

import csv
import random
from datetime import date, timedelta

# brand → (is_lvmh, base share-of-voice weight, profile)
# profile aspect biases are on a -2..+2 scale; they tilt the generated sentiment.
BRANDS = {
    "Louis Vuitton": (True, 18, {"design": 1.5, "quality": 0.6, "price": -1.2, "service": 0.4}),
    "Dior":          (True, 14, {"design": 1.3, "quality": 0.8, "price": -0.6, "service": 0.6}),
    "Tiffany & Co.": (True, 8,  {"design": 1.0, "quality": 1.2, "price": -0.4, "service": 0.8}),
    "Sephora":       (True, 16, {"product": 0.9, "service": -0.8, "price": 0.7, "quality": 0.3}),
    "Fendi":         (True, 6,  {"design": 0.8, "quality": 0.5, "price": -1.5, "service": 0.2}),
    "Chanel":        (False, 15, {"design": 1.6, "quality": 1.0, "price": -1.0, "service": 0.9}),
    "Gucci":         (False, 12, {"design": 0.4, "quality": -0.2, "price": -0.8, "service": 0.1}),
    "Hermès":        (False, 11, {"design": 1.4, "quality": 1.8, "price": -0.3, "service": 1.0}),
}

# aspect → (positive snippets, negative snippets)
ASPECT_SNIPPETS = {
    "quality": (
        ["the craftsmanship is impeccable", "the leather feels buttery and durable",
         "stitching is flawless", "built to last, real investment quality"],
        ["the stitching came loose after a month", "the hardware is already peeling",
         "feels cheap for the price", "it fell apart way too fast"],
    ),
    "design": (
        ["the design is timeless and iconic", "such an elegant silhouette",
         "effortlessly chic", "a true classic that never dates"],
        ["the logo print is way too loud", "looks dated and try-hard",
         "honestly kind of ugly this season", "the design feels lazy"],
    ),
    "price": (
        ["worth every penny", "expensive but justified by the quality",
         "a splurge I do not regret"],
        ["absurdly overpriced", "you are paying for the logo, not the product",
         "the dupe is honestly better for the money", "price hikes are out of control"],
    ),
    "service": (
        ["the sales associate was lovely and attentive", "in-store clienteling was top tier",
         "the boutique experience was seamless"],
        ["the staff was dismissive and rude", "waited 40 minutes and got ignored",
         "terrible after-sales service", "the SA made me feel unwelcome"],
    ),
    "product": (  # beauty / Sephora-flavoured
        ["the formula is incredible and long-lasting", "the shade range is amazing",
         "packaging feels luxe", "my new holy-grail fragrance"],
        ["broke me out instantly", "the scent fades in an hour",
         "shade range is disappointing", "packaging leaked everywhere"],
    ),
}

# trend terms; weight rises or falls across the 12-month window
TREND_TERMS = {
    "quiet luxury": ("rising", ["this is peak quiet luxury", "so quiet-luxury coded"]),
    "old money": ("rising", ["very old-money aesthetic", "screams old money"]),
    "logomania": ("falling", ["logomania is so over", "the logomania era is ending"]),
    "dupe": ("flat", ["found the perfect dupe", "the dupe culture is real"]),
}

NEUTRAL = ["just picked this up", "thoughts?", "saw this in store today",
           "been eyeing this for a while", "unboxing soon"]


def _rating_from_sentiment(sent: float, rng: random.Random) -> int:
    base = 3 + sent * 2 + rng.uniform(-0.6, 0.6)
    return max(1, min(5, round(base)))


def generate_synthetic(n: int = 4000, seed: int = 7, months: int = 12) -> list[dict]:
    rng = random.Random(seed)
    start = date(2024, 1, 1)
    brands = list(BRANDS)
    weights = [BRANDS[b][1] for b in brands]
    platforms = ["xiaohongshu", "weibo", "reddit", "instagram"]
    aspects = list(ASPECT_SNIPPETS)
    out: list[dict] = []
    for _ in range(n):
        brand = rng.choices(brands, weights=weights, k=1)[0]
        is_lvmh, _, profile = BRANDS[brand]
        # date over the window
        day_offset = rng.randint(0, months * 30 - 1)
        d = start + timedelta(days=day_offset)
        month_frac = day_offset / (months * 30)  # 0..1 across window
        # choose an aspect this brand is likely to be discussed on
        aspect = rng.choice(aspects)
        if brand != "Sephora" and aspect == "product":
            aspect = "quality"
        if brand == "Sephora" and aspect in ("design",):
            aspect = "product"
        bias = profile.get(aspect, 0.0)
        # probability of positive snippet driven by aspect bias
        p_pos = 0.5 + bias * 0.18
        pos, neg = ASPECT_SNIPPETS[aspect]
        if rng.random() < p_pos:
            snippet, polarity = rng.choice(pos), 1
        else:
            snippet, polarity = rng.choice(neg), -1
        parts = [snippet]
        # occasionally attach a trend term, weighted by time for rising/falling
        if rng.random() < 0.28:
            term = rng.choice(list(TREND_TERMS))
            direction, phrases = TREND_TERMS[term]
            keep = {"rising": month_frac, "falling": 1 - month_frac, "flat": 0.5}[direction]
            if rng.random() < keep:
                parts.append(rng.choice(phrases))
        elif rng.random() < 0.15:
            parts.append(rng.choice(NEUTRAL)); polarity = polarity  # filler
        text = f"{brand}: " + ", ".join(parts) + "."
        sent = polarity * rng.uniform(0.4, 1.0)
        out.append({
            "brand": brand,
            "text": text,
            "date": d.isoformat(),
            "rating": _rating_from_sentiment(sent, rng),
            "product": aspect,
            "platform": rng.choice(platforms),
        })
    out.sort(key=lambda r: r["date"])
    return out


# ----------------------------------------------------------------- real adapters
def _norm(s: str) -> str:
    return (s or "").strip()


def load_csv(path: str, schema: str = "generic", brand_map: dict | None = None) -> list[dict]:
    """Load a real CSV into the record schema.

    schema="generic": expects columns brand,text,date[,rating,product,platform]
    schema="sephora":  the Kaggle Sephora reviews dataset
        (review_text, rating, brand_name, product_name, submission_time)
    """
    rows: list[dict] = []
    with open(path, newline="", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        cols = {c.lower(): c for c in (reader.fieldnames or [])}

        def pick(*names):
            for n in names:
                if n in cols:
                    return cols[n]
            return None

        if schema == "womens":
            # Women's E-Commerce Clothing Reviews — single anonymised retailer, no brand
            # column; use the product "Class Name" as the comparison dimension.
            c_text = pick("review text", "review_text", "text")
            c_brand = pick("class name", "class")
            c_rating = pick("rating", "stars")
            c_prod = pick("department name", "department")
            c_date = None
        elif schema == "sephora":
            c_text = pick("review_text", "review", "text")
            c_brand = pick("brand_name", "brand")
            c_rating = pick("rating", "stars")
            c_prod = pick("product_name", "product")
            c_date = pick("submission_time", "date", "review_date")
        else:
            c_text = pick("text", "review", "content", "body")
            c_brand = pick("brand", "brand_name")
            c_rating = pick("rating", "stars", "score")
            c_prod = pick("product", "product_name")
            c_date = pick("date", "submission_time", "created", "timestamp")

        for r in reader:
            text = _norm(r.get(c_text, "")) if c_text else ""
            if not text:
                continue
            brand = _norm(r.get(c_brand, "")) if c_brand else "Unknown"
            if brand_map:
                brand = brand_map.get(brand, brand)
            rating = None
            if c_rating and _norm(r.get(c_rating, "")):
                try:
                    rating = float(r[c_rating])
                except ValueError:
                    rating = None
            d = _norm(r.get(c_date, "")) if c_date else ""
            d = d[:10] if d else ""
            rows.append({
                "brand": brand or "Unknown",
                "text": text,
                "date": d,
                "rating": rating,
                "product": _norm(r.get(c_prod, "")) if c_prod else "",
                "platform": "review",
            })
    return rows
