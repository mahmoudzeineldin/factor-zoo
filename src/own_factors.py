# momentum and low volatility built from daily prices, then compared with the published versions
# the signal for month t only uses prices up to the end of t, and the return is earned in t+1
import numpy as np
import pandas as pd
import statsmodels.api as sm

import config


def monthly_prices(daily):
    return daily.resample("ME").last()


# return from 12 months ago to 1 month ago, skipping the latest month
def momentum_signal(daily):
    p = monthly_prices(daily)
    return p.shift(1) / p.shift(12) - 1


# minus last month's volatility, so calm stocks rank high
def low_vol_signal(daily):
    rets = daily.pct_change(fill_method=None)
    vol = rets.rolling(config.VOL_DAYS, min_periods=config.VOL_DAYS - 5).std()
    return -vol.resample("ME").last()


# long the top fifth, short the bottom fifth, equal weights. returns are dated by the month they're earned in
def long_short(signal, daily):
    p = monthly_prices(daily)
    next_ret = p.pct_change(fill_method=None).shift(-1)

    weights = pd.DataFrame(0.0, index=signal.index, columns=signal.columns)
    for date in signal.index:
        s = signal.loc[date].where(next_ret.loc[date].notna()).dropna()
        if len(s) < config.MIN_STOCKS:
            continue
        rank = s.rank(pct=True)
        top = rank[rank > 1 - config.QUANTILE].index
        bottom = rank[rank <= config.QUANTILE].index
        weights.loc[date, top] = 1 / len(top)
        weights.loc[date, bottom] = -1 / len(bottom)

    live = weights.abs().sum(axis=1) > 0
    gross = (weights * next_ret.fillna(0)).sum(axis=1)
    turnover = weights.diff().abs().sum(axis=1)
    net = gross - turnover * config.COST_BPS / 1e4
    out = pd.DataFrame({"gross": gross, "net": net, "turnover": turnover})[live]
    out.index = out.index + pd.offsets.MonthEnd(1)
    return out


def describe(run):
    rows = {}
    for kind in ("gross", "net"):
        r = run[kind]
        rows[f"mean monthly return, {kind}"] = r.mean()
        rows[f"t, {kind}"] = r.mean() / (r.std() / np.sqrt(len(r)))
        rows[f"Sharpe, {kind}"] = r.mean() / r.std() * np.sqrt(12)
    rows["avg monthly turnover"] = run["turnover"].mean()
    rows["months"] = len(run)
    return rows


# how closely my version tracks the published one
def compare(own, published, name):
    d = pd.concat([own.rename("own"), published.rename("pub")], axis=1).dropna()
    if len(d) < 24:
        return None
    model = sm.OLS(d["own"], sm.add_constant(d["pub"])).fit()
    return {"published series": name, "months": len(d),
            "correlation": d["own"].corr(d["pub"]),
            "beta on published": model.params["pub"],
            "monthly alpha vs published": model.params["const"],
            "alpha t": model.tvalues["const"]}


def run_own_factors(daily, ff, all_ls):
    runs = {"momentum (12-2)": long_short(momentum_signal(daily), daily),
            "low volatility (1 month)": long_short(low_vol_signal(daily), daily)}
    stats = pd.DataFrame({name: describe(run) for name, run in runs.items()}).T
    stats = stats.reset_index(names="factor")

    targets = {"momentum (12-2)": [("French UMD", ff.get("UMD")),
                                   ("OSAP Mom12m", all_ls.get("Mom12m"))],
               "low volatility (1 month)": [("OSAP RealizedVol", all_ls.get("RealizedVol")),
                                            ("OSAP IdioVol3F", all_ls.get("IdioVol3F"))]}
    rows = []
    for name, pairs in targets.items():
        for label, series in pairs:
            if series is None:
                continue
            result = compare(runs[name]["gross"], series, label)
            if result:
                rows.append({"factor": name, **result})
    return runs, stats, pd.DataFrame(rows)
