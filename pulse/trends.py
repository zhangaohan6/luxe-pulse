"""Share-of-voice, net sentiment, trending terms, and a buzz×sentiment quadrant."""
from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

from .sentiment import score, tokenize

STOP = set("""a an the and or but to of in on for with at by from this that these those
is are was were be been being it its as i you we they he she my your our their me us
just so very really too also more most so-called got get really thoughts been eyeing
picked today soon""".split())

# multi-word themes to track explicitly
THEMES = ["quiet luxury", "old money", "logomania", "dupe", "investment"]
# component words of the themes — excluded from unigram rising-terms to avoid fragments
_THEME_WORDS = set(w for t in THEMES for w in t.split()) | {
    "quiet-luxury", "peak", "coded", "screams", "era", "ending"}


def share_of_voice(records: list[dict]) -> list[tuple]:
    c = Counter(r["brand"] for r in records)
    total = sum(c.values()) or 1
    return sorted(((b, n, round(n / total, 4)) for b, n in c.items()),
                  key=lambda x: x[1], reverse=True)


def net_sentiment_by_brand(records: list[dict]) -> list[tuple]:
    acc = defaultdict(lambda: [0, 0.0])
    for r in records:
        s = r.get("sentiment")
        if s is None:
            s = score(r["text"])
        acc[r["brand"]][0] += 1
        acc[r["brand"]][1] += s
    rows = [(b, n, round(tot / n, 3)) for b, (n, tot) in acc.items() if n]
    return sorted(rows, key=lambda x: x[2], reverse=True)


def _month(r: dict) -> str:
    return (r.get("date") or "")[:7]  # YYYY-MM


def theme_share(records: list[dict]) -> dict:
    """{theme: count} across all records (substring match, case-insensitive)."""
    low = [r["text"].lower() for r in records]
    return {t: sum(t in x for x in low) for t in THEMES}


def theme_momentum(records: list[dict]) -> list[tuple]:
    """Track the explicit multi-word THEMES: (theme, recent%, early%, lift), lift desc."""
    months = sorted({_month(r) for r in records if _month(r)})
    if len(months) < 3:
        sh = theme_share(records)
        tot = len(records) or 1
        return sorted(((t, round(n / tot, 4), 0.0, 0.0) for t, n in sh.items()),
                      key=lambda x: x[1], reverse=True)
    third = max(1, len(months) // 3)
    early_m, recent_m = set(months[:third]), set(months[-third:])
    early = [r["text"].lower() for r in records if _month(r) in early_m]
    recent = [r["text"].lower() for r in records if _month(r) in recent_m]
    te, tr = len(early) or 1, len(recent) or 1
    rows = []
    for t in THEMES:
        es = sum(t in x for x in early) / te
        rs = sum(t in x for x in recent) / tr
        lift = (rs + 1e-6) / (es + 1e-6)
        rows.append((t, round(rs, 4), round(es, 4), round(lift, 2)))
    rows.sort(key=lambda x: x[3], reverse=True)
    return rows


def rising_terms(records: list[dict], top: int = 12) -> list[tuple]:
    """Compare term frequency in the most recent third vs the earliest third.

    Returns (term, recent_share, early_share, lift) sorted by lift desc.
    Includes the multi-word THEMES plus salient unigrams.
    """
    months = sorted({_month(r) for r in records if _month(r)})
    if len(months) < 3:
        # fall back: just frequency
        c = _term_counts(records)
        tot = sum(c.values()) or 1
        return [(t, round(n / tot, 4), 0.0, 0.0) for t, n in c.most_common(top)]
    third = max(1, len(months) // 3)
    early_m, recent_m = set(months[:third]), set(months[-third:])
    early = [r for r in records if _month(r) in early_m]
    recent = [r for r in records if _month(r) in recent_m]
    ce, cr = _term_counts(early), _term_counts(recent)
    te, tr = sum(ce.values()) or 1, sum(cr.values()) or 1
    terms = set(ce) | set(cr)
    rows = []
    for t in terms:
        es, rs = ce.get(t, 0) / te, cr.get(t, 0) / tr
        if cr.get(t, 0) + ce.get(t, 0) < 8:   # ignore rare noise
            continue
        lift = (rs + 1e-6) / (es + 1e-6)
        rows.append((t, round(rs, 4), round(es, 4), round(lift, 2)))
    rows.sort(key=lambda x: x[3], reverse=True)
    return rows[:top]


def _term_counts(records: list[dict]) -> Counter:
    c = Counter()
    for r in records:
        low = r["text"].lower()
        for theme in THEMES:                  # count multi-word themes
            if theme in low:
                c[theme] += 1
        for w in tokenize(r["text"]):         # salient unigrams (skip theme fragments)
            if len(w) > 3 and w not in STOP and w not in _THEME_WORDS:
                c[w] += 1
    return c


def buzz_vs_sentiment(records: list[dict]) -> list[dict]:
    """Per brand: volume (buzz) + net sentiment, with a quadrant label.

    high buzz + low sentiment  → 'WATCH' (loud but disliked → reputational risk)
    high buzz + high sentiment → 'WINNING'
    low buzz  + high sentiment → 'HIDDEN GEM'
    low buzz  + low sentiment  → 'LAGGING'
    """
    sov = {b: (n, sh) for b, n, sh in share_of_voice(records)}
    sent = {b: s for b, _, s in net_sentiment_by_brand(records)}
    vols = [n for n, _ in sov.values()]
    med_vol = sorted(vols)[len(vols) // 2] if vols else 0
    out = []
    for b in sov:
        n, sh = sov[b]
        s = sent.get(b, 0.0)
        hi_buzz, hi_sent = n >= med_vol, s >= 0
        quad = ("WINNING" if hi_buzz and hi_sent else
                "WATCH" if hi_buzz and not hi_sent else
                "HIDDEN GEM" if hi_sent else "LAGGING")
        out.append({"brand": b, "mentions": n, "sov": sh,
                    "sentiment": round(s, 3), "quadrant": quad})
    out.sort(key=lambda x: x["mentions"], reverse=True)
    return out


def top_products(records: list[dict], top: int = 8) -> list[tuple]:
    c = Counter(r.get("product") for r in records if r.get("product"))
    return c.most_common(top)
