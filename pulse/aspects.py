"""Aspect-based sentiment: which dimensions (quality, design, price, service,
product/beauty, sizing) is a brand winning or losing on?

This is the analysis a luxury brand-insight or CRM team actually wants: not just
"sentiment is 0.3" but "loved for design, hated for price".
"""
from __future__ import annotations

from collections import defaultdict

from .sentiment import score, tokenize

# aspect → trigger keywords
ASPECTS = {
    "quality":  ["quality", "craftsmanship", "leather", "stitching", "hardware",
                 "durable", "material", "peeling", "flimsy", "fell", "loose"],
    "design":   ["design", "style", "silhouette", "logo", "logomania", "iconic",
                 "timeless", "classic", "chic", "ugly", "dated", "aesthetic"],
    "price":    ["price", "expensive", "overpriced", "worth", "value", "investment",
                 "splurge", "dupe", "cheap", "hikes", "money"],
    "service":  ["service", "staff", "associate", "sa", "boutique", "store",
                 "clienteling", "rude", "dismissive", "after-sales"],
    "product":  ["formula", "shade", "fragrance", "scent", "packaging", "skincare",
                 "makeup", "perfume", "broke"],
    "sizing":   ["size", "sizing", "fit", "small", "large", "tight"],
}


def detect_aspects(text: str) -> list[str]:
    toks = set(tokenize(text))
    found = []
    for aspect, kws in ASPECTS.items():
        if toks & set(kws):
            found.append(aspect)
    return found


def aspect_sentiment(records: list[dict]) -> dict:
    """Return {brand: {aspect: {'n': int, 'sentiment': float}}} and an overall row."""
    acc = defaultdict(lambda: defaultdict(lambda: [0, 0.0]))  # brand->aspect->[n, sum]
    overall = defaultdict(lambda: [0, 0.0])
    for r in records:
        s = r.get("sentiment")
        if s is None:
            s = score(r["text"])
        for a in detect_aspects(r["text"]):
            acc[r["brand"]][a][0] += 1
            acc[r["brand"]][a][1] += s
            overall[a][0] += 1
            overall[a][1] += s
    result = {}
    for brand, amap in acc.items():
        result[brand] = {a: {"n": n, "sentiment": round(tot / n, 3)}
                         for a, (n, tot) in amap.items() if n}
    result["_overall"] = {a: {"n": n, "sentiment": round(tot / n, 3)}
                          for a, (n, tot) in overall.items() if n}
    return result


def aspect_leaders(records: list[dict], aspect: str, min_n: int = 15) -> list[tuple]:
    """Brands ranked by sentiment on one aspect (n >= min_n), best first."""
    data = aspect_sentiment(records)
    rows = []
    for brand, amap in data.items():
        if brand == "_overall":
            continue
        cell = amap.get(aspect)
        if cell and cell["n"] >= min_n:
            rows.append((brand, cell["sentiment"], cell["n"]))
    rows.sort(key=lambda x: x[1], reverse=True)
    return rows
