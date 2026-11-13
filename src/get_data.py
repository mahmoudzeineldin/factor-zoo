# downloads everything into data/raw (--skip-prices skips the slow stock price download)
import argparse
import urllib.parse
import urllib.request

import pandas as pd

import config
from french import read_french_zip

SIGNAL_DOC = "https://raw.githubusercontent.com/OpenSourceAP/CrossSection/master/SignalDoc.csv"
OSAP_FILE = "Portfolios/Full Sets OP/PredictorPortsFull.parquet"
HF = "https://huggingface.co/datasets/OpenSourceAP/CrossSection/resolve"
FRENCH = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
SP500 = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(request, timeout=120).read()


def get_osap(raw):
    (raw / "SignalDoc.csv").write_bytes(fetch(SIGNAL_DOC))
    for release in config.OSAP_RELEASES:
        url = f"{HF}/{urllib.parse.quote(release, safe='')}/{urllib.parse.quote(OSAP_FILE)}"
        try:
            (raw / "PredictorPortsFull.parquet").write_bytes(fetch(url))
        except Exception as err:
            print(f"Release {release} not available ({err})")
            continue
        table = pd.read_parquet(raw / "PredictorPortsFull.parquet")
        print(f"Open Source Asset Pricing release {release}: {len(table):,} rows, "
              f"columns {list(table.columns)}")
        return
    raise RuntimeError("Could not download the Open Source Asset Pricing portfolios.")


def get_french(raw):
    five = read_french_zip(fetch(FRENCH + "F-F_Research_Data_5_Factors_2x3_CSV.zip"))
    mom = read_french_zip(fetch(FRENCH + "F-F_Momentum_Factor_CSV.zip"))
    mom.columns = ["UMD"]
    factors = five.join(mom, how="inner").rename(columns={"Mkt-RF": "MKT"})
    factors.to_csv(raw / "ff_factors.csv")
    print(f"French factors {list(factors.columns)}, "
          f"{factors.index.min():%Y-%m} to {factors.index.max():%Y-%m}")


def get_prices(raw):
    import yfinance as yf
    members = pd.read_csv(SP500)
    # Yahoo writes share classes with a dash: BRK.B is BRK-B
    tickers = sorted(members["Symbol"].str.replace(".", "-", regex=False))
    data = yf.download(tickers, start=config.PRICE_START, auto_adjust=True, progress=False)
    close = data["Close"].dropna(how="all", axis=1).dropna(how="all")
    close.index = pd.to_datetime(close.index).tz_localize(None)
    close.index.name = "date"
    close.to_csv(raw / "prices_daily.csv")
    print(f"Prices for {close.shape[1]} of {len(tickers)} tickers, "
          f"{close.index.min():%Y-%m-%d} to {close.index.max():%Y-%m-%d}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-prices", action="store_true")
    args = parser.parse_args()
    raw = config.raw_dir()
    raw.mkdir(parents=True, exist_ok=True)
    get_osap(raw)
    get_french(raw)
    if not args.skip_prices:
        get_prices(raw)


if __name__ == "__main__":
    main()
