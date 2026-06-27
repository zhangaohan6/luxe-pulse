"""Lexicon-based sentiment scoring, luxury-tuned.

Zero-dependency. Returns a compound score in [-1, 1] with negation and
intensifier handling — transparent and auditable (no opaque model), which is
exactly what a brand-insight team wants to trust the numbers.
"""
from __future__ import annotations

import re

POSITIVE = {
    "love", "loved", "lovely", "amazing", "incredible", "impeccable", "flawless",
    "elegant", "chic", "timeless", "iconic", "classic", "beautiful", "gorgeous",
    "durable", "buttery", "luxe", "luxurious", "stunning", "perfect", "worth",
    "investment", "attentive", "seamless", "long-lasting", "holy-grail", "justified",
    "exquisite", "craftsmanship", "premium", "top", "splurge",
}
NEGATIVE = {
    "cheap", "overpriced", "absurdly", "loud", "dated", "ugly", "lazy", "rude",
    "dismissive", "ignored", "terrible", "disappointing", "disappointed", "leaked",
    "broke", "peeling", "loose", "fell", "fake", "scratched", "unwelcome", "over",
    "fades", "faded", "hikes", "try-hard", "unhappy", "regret", "poor", "flimsy",
    "tacky", "knockoff", "dupe",
}
INTENSIFIERS = {"very": 1.5, "so": 1.4, "really": 1.4, "absurdly": 1.6, "way": 1.4,
                "incredibly": 1.6, "extremely": 1.7, "super": 1.4}
NEGATORS = {"not", "no", "never", "isn't", "wasn't", "don't", "didn't", "nothing",
            "hardly", "barely"}

_WORD = re.compile(r"[a-z][a-z'\-]+")


def tokenize(text: str) -> list[str]:
    return _WORD.findall((text or "").lower())


def score(text: str) -> float:
    """Compound sentiment in [-1, 1]."""
    toks = tokenize(text)
    if not toks:
        return 0.0
    total = 0.0
    hits = 0
    for i, w in enumerate(toks):
        val = 0.0
        if w in POSITIVE:
            val = 1.0
        elif w in NEGATIVE:
            val = -1.0
        if val == 0.0:
            continue
        # intensifier in the preceding two tokens
        mult = 1.0
        for j in (i - 1, i - 2):
            if j >= 0 and toks[j] in INTENSIFIERS:
                mult *= INTENSIFIERS[toks[j]]
        # negation flips polarity within a 3-token window before
        for j in range(max(0, i - 3), i):
            if toks[j] in NEGATORS:
                val = -val * 0.9
                break
        total += val * mult
        hits += 1
    if hits == 0:
        return 0.0
    raw = total / hits
    # squash to [-1, 1]
    return max(-1.0, min(1.0, raw))


def label(s: float, pos=0.15, neg=-0.15) -> str:
    return "positive" if s > pos else "negative" if s < neg else "neutral"


def score_records(records: list[dict]) -> list[dict]:
    """Attach a 'sentiment' float and 'sentiment_label' to each record (in place-ish)."""
    out = []
    for r in records:
        s = score(r["text"])
        out.append({**r, "sentiment": s, "sentiment_label": label(s)})
    return out
