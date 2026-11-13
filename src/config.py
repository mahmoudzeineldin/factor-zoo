from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# Open Source Asset Pricing releases to try, newest first
OSAP_RELEASES = ["Data-Release-2026.10", "2025.10", "2024.10"]

# usual t-stat cutoff and the stricter one from Harvey, Liu and Zhu (2016)
T_USUAL = 1.96
T_STRICT = 3.0

# a factor needs this many months in a period before it is tested there
MIN_MONTHS_IN_SAMPLE = 60
MIN_MONTHS_POST_PUB = 24

# settings for the two factors built from prices
PRICE_START = "2000-01-01"
# long the top fifth, short the bottom fifth
QUANTILE = 0.2
# realized volatility window, in trading days
VOL_DAYS = 21
# skip months with fewer stocks than this
MIN_STOCKS = 50
# trading cost per unit of turnover, in basis points
COST_BPS = 10


def raw_dir(fake=False):
    return DATA / ("fake_raw" if fake else "raw")


def out_dir(fake=False):
    return ROOT / ("results_fake" if fake else "results")
