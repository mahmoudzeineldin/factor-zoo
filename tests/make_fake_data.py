# fake data with known answers, to check the code before using real data
# 120 real factors that decay after their sample and after publication, plus 80 pure noise factors
# prices are pure noise, and the published momentum and volatility are computed separately to compare against
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import config

N_REAL, N_NOISE = 120, 80


# separate from src/own_factors.py on purpose, so the check is independent
def simple_long_short(score, next_ret, share):
    out = {}
    for t in range(len(score)):
        s, r = score[t], next_ret[t]
        ok = ~np.isnan(s) & ~np.isnan(r)
        if ok.sum() < 20:
            continue
        order = np.argsort(s[ok])
        k = int(ok.sum() * share)
        out[t] = r[ok][order[-k:]].mean() - r[ok][order[:k]].mean()
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--post-sample", type=float, default=0.25)
    parser.add_argument("--post-pub", type=float, default=0.50)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    rng = np.random.default_rng(args.seed)
    raw = config.raw_dir(fake=True)
    raw.mkdir(parents=True, exist_ok=True)

    months = pd.date_range("1965-01-31", "2025-12-31", freq="ME")
    names = [f"F{i:03d}" for i in range(N_REAL + N_NOISE)]
    end_year = rng.integers(1988, 2011, len(names))
    doc = pd.DataFrame({"Acronym": names, "Cat.Signal": "Predictor", "Authors": "Made up",
                        "Year": end_year + rng.integers(2, 5, len(names)),
                        "SampleStartYear": end_year - 24, "SampleEndYear": end_year,
                        "T-Stat": np.nan})
    true_mean = np.r_[rng.uniform(0.004, 0.009, N_REAL), np.zeros(N_NOISE)]

    # the six benchmark factors, and a shock that all factors share a little of
    ff = pd.DataFrame(rng.normal(0.003, 0.03, (len(months), 6)), index=months,
                      columns=["MKT", "SMB", "HML", "RMW", "CMA", "UMD"])
    ff.index.name = "date"
    common = rng.normal(0, 0.003, len(months))

    long_rows = []
    for i, name in enumerate(names):
        year = months.year
        scale = np.ones(len(months))
        scale[(year > doc.loc[i, "SampleEndYear"]) & (year <= doc.loc[i, "Year"])] = 1 - args.post_sample
        scale[year > doc.loc[i, "Year"]] = 1 - args.post_pub
        r = true_mean[i] * scale + common + rng.normal(0, 0.028, len(months))
        # written in percent with one extra portfolio, like the real file
        long_rows.append(pd.DataFrame({"signalname": name, "port": "LS", "date": months, "ret": r * 100}))
        long_rows.append(pd.DataFrame({"signalname": name, "port": "01", "date": months, "ret": 1.0}))

    # stock prices that are pure noise
    days = pd.bdate_range("2000-01-03", "2025-12-31")
    tickers = [f"S{i:03d}" for i in range(120)]
    vol = rng.uniform(0.008, 0.03, len(tickers))
    daily_ret = rng.normal(0.0003, 1, (len(days), len(tickers))) * vol
    # volatility that drifts, so last month's volatility is informative
    daily_ret *= np.exp(np.cumsum(rng.normal(0, 0.01, daily_ret.shape), axis=0) * 0.3)
    prices = pd.DataFrame(50 * np.exp(np.cumsum(daily_ret, axis=0)), index=days, columns=tickers)
    prices.index.name = "date"

    # "published" momentum and volatility from the same prices, by separate code
    mp = prices.resample("ME").last()
    p = mp.values
    next_ret = np.full(p.shape, np.nan)
    next_ret[:-1] = p[1:] / p[:-1] - 1
    mom = np.full(p.shape, np.nan)
    mom[12:] = p[11:-1] / p[:-12] - 1
    dr = pd.DataFrame(daily_ret, index=days)
    minus_vol = -np.vstack([dr[dr.index.to_period("M") == m.to_period("M")].std().values for m in mp.index])
    for label, score, share in [("Mom12m", mom, 0.3), ("RealizedVol", minus_vol, 0.3)]:
        series = simple_long_short(score, next_ret, share)
        dates = [mp.index[t + 1] for t in series]
        values = np.array(list(series.values())) + rng.normal(0, 0.002, len(series))
        long_rows.append(pd.DataFrame({"signalname": label, "port": "LS", "date": dates, "ret": values * 100}))
        if label == "Mom12m":
            ff.loc[dates, "UMD"] = values

    pd.concat(long_rows, ignore_index=True).to_parquet(raw / "PredictorPortsFull.parquet")
    doc.to_csv(raw / "SignalDoc.csv", index=False)
    ff.to_csv(raw / "ff_factors.csv")
    prices.to_csv(raw / "prices_daily.csv")
    planted = {"post_sample": args.post_sample, "post_pub": args.post_pub,
               "n_real": N_REAL, "n_noise": N_NOISE, "real_mean": float(true_mean[:N_REAL].mean())}
    (raw / "planted.json").write_text(json.dumps(planted))
    print(f"Fake data written to {raw}: {planted}")


if __name__ == "__main__":
    main()
