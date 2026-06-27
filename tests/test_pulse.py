import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pulse import aspects, data, trends
from pulse.sentiment import label, score, score_records


def test_sentiment_polarity():
    assert score("the craftsmanship is impeccable and timeless") > 0.2
    assert score("absurdly overpriced and the stitching came loose") < -0.2


def test_sentiment_negation():
    pos = score("the quality is amazing")
    neg = score("the quality is not amazing")
    assert pos > 0 and neg < pos


def test_label_bands():
    assert label(0.5) == "positive"
    assert label(-0.5) == "negative"
    assert label(0.0) == "neutral"


def test_aspect_detection():
    a = aspects.detect_aspects("the leather stitching is flawless but overpriced")
    assert "quality" in a and "price" in a


def test_sov_sums_to_one():
    recs = data.generate_synthetic(n=800, seed=1)
    sov = trends.share_of_voice(recs)
    assert abs(sum(sh for _, _, sh in sov) - 1.0) < 1e-2   # shares rounded to 4dp
    assert sum(n for _, n, _ in sov) == len(recs)


def test_quiet_luxury_is_rising():
    recs = data.generate_synthetic(n=4000, seed=7)
    mom = {t: lift for t, _, _, lift in trends.theme_momentum(recs)}
    assert mom["quiet luxury"] > 1.3          # injected rising theme detected
    assert mom["logomania"] < 0.9             # injected falling theme detected


def test_buzz_quadrant_labels():
    recs = score_records(data.generate_synthetic(n=2000, seed=3))
    q = trends.buzz_vs_sentiment(recs)
    labels = {r["quadrant"] for r in q}
    assert labels <= {"WINNING", "WATCH", "HIDDEN GEM", "LAGGING"}
    assert all("brand" in r and "sentiment" in r for r in q)


def test_sephora_csv_adapter(tmp_path):
    p = tmp_path / "s.csv"
    p.write_text(
        "review_text,rating,brand_name,product_name,submission_time\n"
        "the formula is incredible,5,Sephora Collection,Lip Oil,2024-03-01\n"
        "broke me out instantly,2,Dior,Forever Foundation,2024-04-02\n",
        encoding="utf-8",
    )
    recs = data.load_csv(str(p), schema="sephora")
    assert len(recs) == 2
    assert recs[0]["brand"] == "Sephora Collection"
    assert recs[0]["date"] == "2024-03-01"
    assert recs[1]["rating"] == 2.0
