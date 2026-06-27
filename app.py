"""Streamlit dashboard for luxe-pulse.

Run:  streamlit run app.py     (needs: pip install streamlit pandas)
"""
import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))

from pulse import aspects, data, trends
from pulse.data import BRANDS
from pulse.sentiment import score_records

st.set_page_config(page_title="Luxe Pulse", page_icon="👜", layout="wide")
st.title("👜 Luxe Pulse — Luxury Brand Social & Review Analytics")
st.caption("Sentiment · share-of-voice · aspect leaders · theme momentum — LVMH maisons vs peers")

with st.sidebar:
    st.header("Data")
    up = st.file_uploader("Review/social CSV (optional)", type="csv")
    schema = st.selectbox("CSV schema", ["generic", "sephora"])
    n = st.slider("Synthetic sample size", 1000, 8000, 4000, 500)

if up is not None:
    os.makedirs("out", exist_ok=True)
    tmp = os.path.join("out", "_up.csv")
    with open(tmp, "wb") as f:
        f.write(up.getvalue())
    recs = data.load_csv(tmp, schema=schema)
    st.sidebar.success(f"Loaded {len(recs):,} real rows")
else:
    recs = data.generate_synthetic(n=n)

recs = score_records(recs)
df = pd.DataFrame(recs)

sov = pd.DataFrame(trends.share_of_voice(recs), columns=["brand", "mentions", "sov"])
sent = pd.DataFrame(trends.net_sentiment_by_brand(recs), columns=["brand", "n", "sentiment"])
quad = pd.DataFrame(trends.buzz_vs_sentiment(recs))

c1, c2, c3 = st.columns(3)
c1.metric("Posts / reviews", f"{len(recs):,}")
c2.metric("Brands", df["brand"].nunique())
watch = quad[quad["quadrant"] == "WATCH"]["brand"].tolist()
c3.metric("On reputational watch", len(watch), ", ".join(watch) or "none")

t1, t2, t3, t4 = st.tabs(["Share of voice", "Sentiment", "Aspects", "Theme momentum"])

with t1:
    st.bar_chart(sov.set_index("brand")["sov"])
    st.dataframe(sov, use_container_width=True)

with t2:
    st.bar_chart(sent.set_index("brand")["sentiment"])
    st.subheader("Buzz × sentiment quadrant")
    st.dataframe(quad, use_container_width=True)

with t3:
    am = aspects.aspect_sentiment(recs)
    rows = []
    for brand, amap in am.items():
        if brand == "_overall":
            continue
        for asp, cell in amap.items():
            rows.append({"brand": brand, "aspect": asp,
                         "sentiment": cell["sentiment"], "n": cell["n"]})
    adf = pd.DataFrame(rows)
    if not adf.empty:
        pivot = adf.pivot_table(index="brand", columns="aspect", values="sentiment")
        st.dataframe(pivot.style.format("{:+.2f}", na_rep="—"), use_container_width=True)

with t4:
    mom = pd.DataFrame(trends.theme_momentum(recs),
                       columns=["theme", "recent", "early", "lift"])
    st.dataframe(mom, use_container_width=True)
    st.bar_chart(mom.set_index("theme")["lift"])
