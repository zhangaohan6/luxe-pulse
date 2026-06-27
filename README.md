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

## Use real data (recommended — real findings)

The engine reads any review/social CSV. The natural fit is the **Sephora reviews** dataset
on Kaggle (Sephora = LVMH):

```bash
# download "Sephora Products and Skincare Reviews" from Kaggle → reviews.csv
python3 analyze_pulse.py --real reviews.csv --schema sephora
```

`--schema generic` expects columns `brand,text,date[,rating,product,platform]`; the loader
auto-maps common column names, so most brand-review / social exports work.

## Demo findings (synthetic, seeded)

> The demo data is **synthetic** and seeded for reproducibility — it deliberately bakes in a
> rising *quiet luxury* theme and a price/service pain point so the pipeline produces a clear
> narrative. **The analysis logic is real**; plug in the Sephora CSV for real-world numbers.

- **LVMH maisons take 4 of the top 5 by share of voice** (LV 18.5%, Sephora 15.9%).
- **Aspect split is the story**: Hermès leads *quality* & *service*; Chanel leads *design*;
  **Louis Vuitton is weakest on *price*** (−0.17); **Sephora is weakest on *service*** (−0.11)
  — an actionable, dimension-specific read, not a single score.
- **Theme momentum**: *quiet luxury* ×7 and *old money* ×4 rising; **logomania falling ×0.27**.

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
