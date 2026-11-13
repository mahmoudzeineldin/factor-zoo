# runs everything and writes results/ (add --fake to use the fake data)
import argparse

import pandas as pd

import charts
import config
import load
from own_factors import run_own_factors
from zoo_tests import (decay_regression, event_time, factor_table, ff_alphas, long_panel,
                       multiple_testing)


def md_table(df, digits=3):
    def show(v):
        if isinstance(v, float):
            if pd.isna(v):
                return ""
            if v.is_integer() and abs(v) >= 10:
                return str(int(v))
            return f"{v:.{digits}f}"
        return str(v)
    head = "| " + " | ".join(str(c) for c in df.columns) + " |"
    rule = "|" + "|".join(["---"] * len(df.columns)) + "|"
    body = ["| " + " | ".join(show(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join([head, rule] + body)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fake", action="store_true")
    fake = parser.parse_args().fake

    out = config.out_dir(fake)
    (out / "tables").mkdir(parents=True, exist_ok=True)
    (out / "figures").mkdir(parents=True, exist_ok=True)

    doc = load.load_signal_doc(fake)
    all_ls = load.load_ls_returns(fake)
    ff = load.load_ff(fake)
    daily = load.load_prices(fake)
    rets = all_ls[[c for c in all_ls.columns if c in doc.index]]
    missing = sorted(set(doc.index) - set(rets.columns))
    print(f"{rets.shape[1]} documented predictors have return data; {len(missing)} do not.")

    table = factor_table(rets, doc)
    counts = multiple_testing(table)
    panel = long_panel(rets, doc)
    decay = decay_regression(panel)
    event = event_time(panel)
    alpha_table, alpha_summary = ff_alphas(rets, doc, ff)

    both = table.dropna(subset=["mean_in", "mean_post"])
    ratio = both["mean_post"].mean() / both["mean_in"].mean()

    tables = {"factors": table.reset_index(), "multiple_testing": counts, "decay": decay,
              "event_time": event.reset_index(), "ff_alphas": alpha_table.reset_index(),
              "ff_alpha_summary": alpha_summary}
    charts.t_stat_chart(table, out / "figures", fake)
    charts.event_time_chart(event, decay.attrs["in_sample_mean"], out / "figures", fake)

    lines = []
    if fake:
        lines += ["# FAKE DATA: these numbers come from made-up returns and mean nothing", ""]
    lines += [
        "# Results", "",
        f"{rets.shape[1]} published predictors, monthly long-short returns "
        f"{rets.index.min():%Y-%m} to {rets.index.max():%Y-%m}.", "",
        "## How many factors pass each bar", "",
        md_table(counts), "",
        "Benjamini-Hochberg and Benjamini-Yekutieli control the false discovery rate at 5%. "
        "Bonferroni controls the chance of any false positive at 5%.", "",
        "## Decay after the sample and after publication", "",
        md_table(decay, digits=4), "",
        f"Average in-sample return: {decay.attrs['in_sample_mean']*100:.3f}% a month. "
        f"{decay.attrs['n']:,} factor-months, factor fixed effects, standard errors clustered by month. "
        f"Across the {len(both)} factors with both periods, the average post-publication return is "
        f"{ratio:.0%} of the average in-sample return.", "",
        "## Beyond Fama-French", "",
        md_table(alpha_summary), "",
        "Each factor is regressed on MKT, SMB, HML, RMW, CMA and UMD over its full history.", "",
    ]

    if daily is not None:
        runs, own_stats, own_compare = run_own_factors(daily, ff, all_ls)
        tables["own_factor_stats"] = own_stats
        tables["own_factor_comparison"] = own_compare
        published = {"momentum (12-2)": ("French UMD", ff["UMD"]) if "UMD" in ff else None,
                     "low volatility (1 month)": ("OSAP RealizedVol", all_ls["RealizedVol"])
                     if "RealizedVol" in all_ls else None}
        charts.own_factor_chart(runs, published, out / "figures", fake)
        lines += ["## Factors built from prices", "",
                  f"{daily.shape[1]} stocks, top and bottom {config.QUANTILE:.0%}, equal weights, "
                  f"{config.COST_BPS} bp cost per unit of turnover.", "",
                  md_table(own_stats, digits=4), "",
                  md_table(own_compare, digits=4) if len(own_compare) else "No published series to compare with.", ""]
    else:
        lines += ["## Factors built from prices", "", "No price file found, so this part was skipped.", ""]

    for name, t in tables.items():
        t.to_csv(out / "tables" / f"{name}.csv", index=False)
    (out / "summary.md").write_text("\n".join(lines))
    print(f"Wrote {out / 'summary.md'}")


if __name__ == "__main__":
    main()
