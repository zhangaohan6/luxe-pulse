# Luxe Pulse — Luxury Brand Social & Review Analytics

A Python tool that turns luxury **social posts / product reviews** into a **brand-insight
brief**: who owns the conversation (share-of-voice), who is loved or disliked (sentiment),
**which dimension each house wins or loses on** (quality / design / price / service /
product), and **which themes are rising or fading** (e.g. *quiet luxury* ↑, *logomania* ↓).
It is the analysis a luxury **consumer-insight / CRM / digital-marketing** team does — made
reproducible and auditable.

Built to combine a **computer-science background** with the **luxury / fashion industry**
(target: LVMH-style data & insight internships). The default brand set contrasts **LVMH
maisons** (Louis Vuitton, Dior, Tiffany & Co., Sephora, Fendi) with peers (Chanel, Gucci,
Hermès), and it ingests the **Sephora reviews** dataset directly — Sephora is an LVMH maison.

## What it computes

- **Share of voice** — each brand's slice of the conversation.
- **Net sentiment** — a transparent, luxury-tuned **lexicon** scorer (negation +
  intensifier aware; no opaque black-box model).
- **Aspect-based sentiment** — sentiment per dimension (quality, design, price, service,
  product), so you see *loved for design, hated for price* — not just one number.
- **Buzz × sentiment quadrant** — `WINNING` / `WATCH` (loud but disliked → reputational
  risk) / `HIDDEN GEM` / `LAGGING`.
- **Theme momentum** — rising/falling tracking of luxury themes over time.

## Quick start

```bash
pip install pandas            # core analysis needs only the stdlib; pandas is for the app
python3 analyze_pulse.py                              # synthetic demo
python3 analyze_pulse.py --brand "Louis Vuitton" "Dior" "Chanel"
streamlit run app.py                                  # interactive dashboard
```

## Use real data

The engine reads any review/social CSV. The natural fit is the **Sephora reviews** dataset
(Sephora is an LVMH retailer):

```bash
python3 analyze_pulse.py --real reviews.csv --schema sephora
```

`--schema generic` expects columns `brand,text,date[,rating,product,platform]`; the loader
auto-maps common column names, so most brand-review / social exports work.

## Validation on real data — 49,918 Sephora reviews

Validated on the **Sephora Products and Skincare Reviews** dataset
([Kaggle](https://www.kaggle.com/datasets/nadyinky/sephora-products-and-skincare-reviews),
public mirror) — **49,918 real customer reviews across 122 prestige-skincare brands**. Run
straight through the same pipeline (no scraping, no manual cleaning):

- **All four LVMH skincare maisons in the data are net-positive** — Fenty Skin **+0.38**,
  Dior **+0.35**, Fresh **+0.34**, Guerlain **+0.27** — useful for an LVMH consumer-insight read.
- **SEPHORA COLLECTION owns the most share of voice** (4.9%, 2,429 reviews) but is the
  **weakest top brand on the *design / packaging* aspect (−0.22)** — high buzz, a specific
  fixable weakness, not a vague score.
- **"dupe" is the rising theme** (×2.58 recent-vs-earlier) — the tool picks up the real
  beauty *dupe-culture* shift straight from review text.
- Aspect leaders differ by dimension (e.g. *price* sentiment led by Youth To The People,
  Sulwhasoo) — exactly the brand-vs-brand, dimension-by-dimension read an insight team needs.

> The repo also ships a **seeded synthetic generator** (`generate_synthetic`) with a baked-in
> *quiet luxury* ↑ / *logomania* ↓ storyline, so `python3 analyze_pulse.py` runs with zero
> setup and the tests are deterministic. The 24 MB review CSV is **not** committed
> (`data/` is git-ignored).

## Layout
```
pulse/
  data.py        # synthetic generator + real CSV adapters (generic / Sephora)
  sentiment.py   # luxury-tuned lexicon sentiment (negation + intensifiers)
  aspects.py     # aspect detection + per-aspect sentiment
  trends.py      # share-of-voice, net sentiment, theme momentum, buzz×sentiment quadrant
  report.py      # markdown brand-insight brief
analyze_pulse.py # CLI (--real, --schema, --brand)
app.py           # Streamlit dashboard
tests/           # 8 unit tests (sentiment, negation, aspects, SOV, theme trends, CSV adapter)
```

## Tests
```bash
python3 -m pytest -q
```

*Author: Aohan Zhang · MIT License*
