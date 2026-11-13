# tests on the published factors: significance, decay after publication, and alphas
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.multitest import multipletests

import config


# label each month: before sample, in sample, post sample or post publication
def period_of(dates, row):
    year = dates.year
    label = pd.Series("before sample", index=dates)
    label[(year >= row.start_year) & (year <= row.end_year)] = "in sample"
    label[(year > row.end_year) & (year <= row.pub_year)] = "post sample"
    label[year > row.pub_year] = "post publication"
    return label


def mean_t(x):
    x = x.dropna()
    if len(x) < 2 or x.std() == 0:
        return np.nan, np.nan, len(x)
    return x.mean(), x.mean() / (x.std() / np.sqrt(len(x))), len(x)


def factor_table(rets, doc):
    rows = []
    for row in doc.itertuples():
        if row.Index not in rets.columns:
            continue
        r = rets[row.Index].dropna()
        label = period_of(r.index, row)
        m_in, t_in, n_in = mean_t(r[label == "in sample"])
        m_post, t_post, n_post = mean_t(r[label == "post publication"])
        m_all, t_all, n_all = mean_t(r)
        rows.append({"factor": row.Index, "pub_year": int(row.pub_year),
                     "end_year": int(row.end_year), "paper_t": row.paper_t,
                     "mean_in": m_in, "t_in": t_in, "n_in": n_in,
                     "mean_post": m_post, "t_post": t_post, "n_post": n_post,
                     "mean_all": m_all, "t_all": t_all, "n_all": n_all})
    table = pd.DataFrame(rows).set_index("factor")
    table.loc[table["n_in"] < config.MIN_MONTHS_IN_SAMPLE, ["mean_in", "t_in"]] = np.nan
    table.loc[table["n_post"] < config.MIN_MONTHS_POST_PUB, ["mean_post", "t_post"]] = np.nan
    return table


# count how many factors pass each cutoff. only positive t-stats count,
# since every factor is signed by its paper to earn a positive return
def count_survivors(t, n_obs, label):
    ok = t.notna()
    t, n_obs = t[ok], n_obs[ok]
    p = 2 * stats.t.sf(t.abs(), n_obs - 1)
    positive = t > 0
    row = {"period": label, "factors tested": len(t),
           f"t > {config.T_USUAL}": int((t > config.T_USUAL).sum()),
           f"t > {config.T_STRICT}": int((t > config.T_STRICT).sum())}
    for name, method in [("Bonferroni", "bonferroni"), ("Benjamini-Hochberg", "fdr_bh"),
                         ("Benjamini-Yekutieli", "fdr_by")]:
        passed = multipletests(p, alpha=0.05, method=method)[0]
        row[name] = int((passed & positive.values).sum())
    return row


def multiple_testing(table):
    rows = [count_survivors(table["t_in"], table["n_in"], "in original sample"),
            count_survivors(table["t_post"], table["n_post"], "after publication"),
            count_survivors(table["t_all"], table["n_all"], "full history")]
    return pd.DataFrame(rows)


def long_panel(rets, doc):
    parts = []
    for row in doc.itertuples():
        if row.Index not in rets.columns:
            continue
        r = rets[row.Index].dropna()
        label = period_of(r.index, row)
        parts.append(pd.DataFrame({"factor": row.Index, "date": r.index, "ret": r.values,
                                   "period": label.values,
                                   "event_year": r.index.year - int(row.pub_year)}))
    panel = pd.concat(parts, ignore_index=True)
    return panel[panel["period"] != "before sample"]


# pooled regression like McLean and Pontiff (2016), clustered by month since factors move together
def decay_regression(panel):
    d = panel.copy()
    d["post_sample"] = (d["period"] == "post sample").astype(float)
    d["post_pub"] = (d["period"] == "post publication").astype(float)
    # taking out each factor's own average is the same as giving it its own intercept
    cols = ["ret", "post_sample", "post_pub"]
    within = d[cols] - d.groupby("factor")[cols].transform("mean")
    model = sm.OLS(within["ret"], within[["post_sample", "post_pub"]]).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(d["date"])[0]})

    base = d.loc[d["period"] == "in sample", "ret"].mean()
    rows = []
    for term, name in [("post_sample", "after sample end, before publication"),
                       ("post_pub", "after publication")]:
        rows.append({"period": name, "change in monthly return": model.params[term],
                     "t": model.tvalues[term],
                     "change as share of in-sample mean": model.params[term] / base})
    out = pd.DataFrame(rows)
    out.attrs["in_sample_mean"] = base
    out.attrs["n"] = int(model.nobs)
    return out


# average return by year relative to publication
def event_time(panel, window=15):
    d = panel[panel["event_year"].between(-window, window)]
    per_factor = d.groupby(["event_year", "factor"])["ret"].mean()
    return per_factor.groupby("event_year").agg(["mean", "count"])


# alpha against the Fama-French five factors plus momentum
def ff_alphas(rets, doc, ff):
    names = ["MKT", "SMB", "HML", "RMW", "CMA", "UMD"]
    rows = []
    for factor in doc.index.intersection(rets.columns):
        d = pd.concat([rets[factor], ff[names]], axis=1).dropna()
        if len(d) < config.MIN_MONTHS_IN_SAMPLE:
            continue
        model = sm.OLS(d[factor], sm.add_constant(d[names])).fit()
        rows.append({"factor": factor, "alpha": model.params["const"],
                     "alpha_t": model.tvalues["const"], "r2": model.rsquared, "n": len(d)})
    table = pd.DataFrame(rows).set_index("factor")
    summary = pd.DataFrame([{
        "factors tested": len(table),
        f"raw mean t > {config.T_USUAL}": int((mean_ts(rets, table.index, ff.index) > config.T_USUAL).sum()),
        f"alpha t > {config.T_USUAL}": int((table["alpha_t"] > config.T_USUAL).sum()),
        f"alpha t > {config.T_STRICT}": int((table["alpha_t"] > config.T_STRICT).sum()),
        "median R2": table["r2"].median()}])
    return table, summary


# raw mean t-stat over the same months as the alpha regression
def mean_ts(rets, factors, dates):
    sub = rets.loc[rets.index.intersection(dates), list(factors)]
    return sub.mean() / (sub.std() / np.sqrt(sub.count()))
