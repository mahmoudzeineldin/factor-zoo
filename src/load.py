import pandas as pd

import config


def month_end(dates):
    return pd.DatetimeIndex(pd.to_datetime(dates)) + pd.offsets.MonthEnd(0)


# one row per predictor, with its sample years and publication year
def load_signal_doc(fake=False):
    doc = pd.read_csv(config.raw_dir(fake) / "SignalDoc.csv")
    doc = doc[doc["Cat.Signal"] == "Predictor"]
    doc = doc.rename(columns={"Acronym": "factor", "Year": "pub_year",
                              "SampleStartYear": "start_year", "SampleEndYear": "end_year",
                              "T-Stat": "paper_t"})
    keep = ["factor", "Authors", "pub_year", "start_year", "end_year", "paper_t"]
    doc = doc[keep].dropna(subset=["pub_year", "start_year", "end_year"])
    return doc.set_index("factor")


# monthly long-short returns, one column per factor
def load_ls_returns(fake=False):
    table = pd.read_parquet(config.raw_dir(fake) / "PredictorPortsFull.parquet")
    ls = table[table["port"].astype(str) == "LS"].copy()
    if ls.empty:
        raise ValueError(f"No long-short rows found. Port labels seen: {table['port'].unique()[:12]}")
    ls["date"] = month_end(ls["date"])
    wide = ls.pivot(index="date", columns="signalname", values="ret").sort_index()

    # returns should be in percent, but check before dividing by 100
    typical = wide.abs().median().median()
    if typical > 0.2:
        wide = wide / 100
        print(f"Factor returns read as percent (typical monthly move {typical:.2f}) and divided by 100.")
    else:
        print(f"Factor returns read as decimals (typical monthly move {typical:.4f}).")
    return wide


def load_ff(fake=False):
    ff = pd.read_csv(config.raw_dir(fake) / "ff_factors.csv", parse_dates=["date"], index_col="date")
    ff.index = month_end(ff.index)
    return ff


def load_prices(fake=False):
    path = config.raw_dir(fake) / "prices_daily.csv"
    if not path.exists():
        return None
    return pd.read_csv(path, parse_dates=["date"], index_col="date").sort_index()
