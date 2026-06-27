"""Assemble a markdown brand-insight report from the analysis functions."""
from __future__ import annotations

from . import aspects, trends
from .data import BRANDS


def _lvmh_tag(brand: str) -> str:
    info = BRANDS.get(brand)
    return " · LVMH" if info and info[0] else ""


def build(records: list[dict]) -> str:
    n = len(records)
    sov = trends.share_of_voice(records)
    sent = trends.net_sentiment_by_brand(records)
    quad = trends.buzz_vs_sentiment(records)
    rising = trends.rising_terms(records)
    asp = aspects.aspect_sentiment(records)

    L = [f"# Luxury Brand Pulse — {n:,} posts/reviews\n"]

    L.append("## Share of voice")
    for b, cnt, sh in sov:
        L.append(f"- **{b}**{_lvmh_tag(b)} — {sh*100:.1f}%  ({cnt:,})")

    L.append("\n## Net sentiment (high → low)")
    for b, cnt, s in sent:
        bar = "🟢" if s > 0.15 else "🟡" if s > -0.15 else "🔴"
        L.append(f"- {bar} **{b}**{_lvmh_tag(b)} — {s:+.2f}  (n={cnt:,})")

    L.append("\n## Buzz × sentiment quadrant")
    for row in quad:
        L.append(f"- **{row['brand']}** → `{row['quadrant']}` "
                 f"(sov {row['sov']*100:.1f}%, sentiment {row['sentiment']:+.2f})")
    watch = [r["brand"] for r in quad if r["quadrant"] == "WATCH"]
    if watch:
        L.append(f"\n  ⚠️ **Reputational watch-list** (loud but disliked): {', '.join(watch)}")

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
