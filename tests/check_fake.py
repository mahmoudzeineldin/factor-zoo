# compares the results on fake data with what was planted in it
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import config

raw, out = config.raw_dir(True), config.out_dir(True) / "tables"
planted = json.loads((raw / "planted.json").read_text())
n_all = planted["n_real"] + planted["n_noise"]

decay = pd.read_csv(out / "decay.csv").set_index("period")["change in monthly return"]
# the planted fall applies to real factors only, so the pooled fall is diluted by the noise ones
expect_sample = -planted["post_sample"] * planted["real_mean"] * planted["n_real"] / n_all
expect_pub = -planted["post_pub"] * planted["real_mean"] * planted["n_real"] / n_all
print("Change in monthly return   planted    recovered")
print(f"  after sample end        {expect_sample:+.5f}   {decay.iloc[0]:+.5f}")
print(f"  after publication       {expect_pub:+.5f}   {decay.iloc[1]:+.5f}")
assert abs(decay.iloc[1] - expect_pub) < 0.0006, "post-publication decay is off"
assert abs(decay.iloc[0] - expect_sample) < 0.0008, "post-sample decay is off"

factors = pd.read_csv(out / "factors.csv")
factors["real"] = factors["factor"].str[1:].astype(int) < planted["n_real"]
strict = factors[factors["t_all"] > config.T_STRICT]
usual = factors[factors["t_all"] > config.T_USUAL]
print(f"Full-history t > {config.T_USUAL}: {len(usual)} factors, {(~usual['real']).sum()} of them noise "
      f"(about {planted['n_noise'] * 0.025:.0f} expected by chance)")
print(f"Full-history t > {config.T_STRICT}: {len(strict)} factors, {(~strict['real']).sum()} of them noise")
assert (~strict["real"]).sum() <= 2, "too many noise factors pass the strict bar"
assert strict["real"].sum() > 0.8 * planted["n_real"], "the strict bar is missing real factors"

compare = pd.read_csv(out / "own_factor_comparison.csv")
print(compare[["factor", "published series", "correlation"]].to_string(index=False))
assert (compare["correlation"] > 0.8).all(), "a factor built from prices does not track its planted series"
print("All checks passed.")
