"""Assemble a markdown brand-insight report from the analysis functions."""
from __future__ import annotations

from . import aspects, trends
from .data import BRANDS

# LVMH-owned beauty/skincare maisons (for tagging real prestige-beauty datasets,
# e.g. Sephora reviews — Sephora is itself an LVMH retailer). Matched case-insensitively.
LVMH_BEAUTY = {"dior", "guerlain", "fenty skin", "fenty beauty", "fresh",
               "givenchy", "benefit cosmetics", "make up for ever", "kvd beauty"}


def _lvmh_tag(brand: str) -> str:
    info = BRANDS.get(brand)
    if info and info[0]:
        return " · LVMH"
    return " · LVMH" if (brand or "").strip().lower() in LVMH_BEAUTY else ""


def build(records: list[dict], top_brands: int = 18) -> str:
    n = len(records)
    sov = trends.share_of_voice(records)
    sent = trends.net_sentiment_by_brand(records)
    quad = trends.buzz_vs_sentiment(records)
    rising = trends.rising_terms(records)

    top = [b for b, _, _ in sov[:top_brands]]
    topset = set(top)
    many = len(sov) > top_brands

    L = [f"# Luxury Brand Pulse — {n:,} posts/reviews"]
    if many:
        L.append(f"_{len(sov)} brands in data; showing top {top_brands} by volume._")
    L.append("")

    L.append("## Share of voice" + (f" (top {top_brands})" if many else ""))
    for b, cnt, sh in sov[:top_brands]:
        L.append(f"- **{b}**{_lvmh_tag(b)} — {sh*100:.1f}%  ({cnt:,})")

    L.append("\n## Net sentiment (top brands, high → low)")
    for b, cnt, s in [r for r in sent if r[0] in topset]:
        bar = "🟢" if s > 0.15 else "🟡" if s > -0.15 else "🔴"
        L.append(f"- {bar} **{b}**{_lvmh_tag(b)} — {s:+.2f}  (n={cnt:,})")

    L.append("\n## Buzz × sentiment quadrant (top brands)")
    for row in [r for r in quad if r["brand"] in topset]:
        L.append(f"- **{row['brand']}**{_lvmh_tag(row['brand'])} → `{row['quadrant']}` "
                 f"(sov {row['sov']*100:.1f}%, sentiment {row['sentiment']:+.2f})")
    watch = [r["brand"] for r in quad if r["quadrant"] == "WATCH" and r["brand"] in topset]
    if watch:
        L.append(f"\n  ⚠️ **Reputational watch-list** (loud but disliked): {', '.join(watch)}")

    # LVMH spotlight — surface LVMH maisons present even if outside the top-N by volume
    sov_map = {b: (cnt, sh) for b, cnt, sh in sov}
    sent_map = {b: s for b, _, s in sent}
    lvmh_present = [b for b in sov_map if _lvmh_tag(b)]
    if lvmh_present:
        lvmh_present.sort(key=lambda b: sent_map.get(b, 0), reverse=True)
        L.append("\n## LVMH maisons in this dataset")
        for b in lvmh_present:
            cnt, sh = sov_map[b]
            L.append(f"- **{b}** — sentiment {sent_map.get(b, 0):+.2f}  "
                     f"(sov {sh*100:.2f}%, n={cnt:,})")

    L.append("\n## Aspect leaders (who wins each dimension)")
    for aspect in ["quality", "design", "price", "service", "product"]:
        rows = aspects.aspect_leaders(records, aspect)
        if not rows:
            continue
        best = ", ".join(f"{b} {s:+.2f}" for b, s, _ in rows[:3])
        if len(rows) > 1:
            worst = rows[-1]
            L.append(f"- **{aspect}** — top: {best}  |  weakest: {worst[0]} {worst[1]:+.2f}")
        else:
            L.append(f"- **{aspect}** — {best}")

    L.append("\n## Theme momentum (recent vs earlier window)")
    for term, rs, es, lift in trends.theme_momentum(records):
        arrow = "📈 rising" if lift > 1.25 else "📉 falling" if lift < 0.8 else "➡️ flat"
        L.append(f"- **{term}** — {arrow}  (×{lift};  {es*100:.2f}% → {rs*100:.2f}%)")

    L.append("\n## Other rising terms")
    seen = 0
    for term, rs, es, lift in rising:
        if lift <= 1.25 or seen >= 6 or term in trends.THEMES:
            continue
        L.append(f"- 📈 **{term}** — ×{lift}  ({es*100:.2f}% → {rs*100:.2f}%)")
        seen += 1

    return "\n".join(L) + "\n"
