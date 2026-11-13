import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import config


def save(fig, folder, name, fake):
    if fake:
        fig.suptitle("FAKE DATA")
    fig.tight_layout()
    fig.savefig(folder / name, dpi=150)
    plt.close(fig)


def t_stat_chart(table, folder, fake):
    fig, axes = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    bins = np.arange(-4, 12.5, 0.5)
    for ax, col, name in [(axes[0], "t_in", "inside the original sample"),
                          (axes[1], "t_post", "after publication")]:
        t = table[col].dropna().clip(-4, 12)
        ax.hist(t, bins=bins)
        ax.axvline(config.T_USUAL, color="k", linestyle="--", label=f"t = {config.T_USUAL}")
        ax.axvline(config.T_STRICT, color="r", linestyle="--", label=f"t = {config.T_STRICT:g}")
        ax.set_title(f"t-stats {name} ({len(t)} factors)")
        ax.set_ylabel("number of factors")
        ax.legend()
    axes[1].set_xlabel("t-stat")
    save(fig, folder, "t_stats.png", fake)


def event_time_chart(event, in_sample_mean, folder, fake):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(event.index, event["mean"] * 100, marker="o")
    ax.axhline(in_sample_mean * 100, color="gray", linestyle="--", label="in-sample average")
    ax.axhline(0, color="k", linewidth=0.8)
    ax.axvline(0, color="k", linestyle=":")
    ax.set_xlabel("years from publication")
    ax.set_ylabel("average return (% per month)")
    ax.set_title("Factor returns before and after publication")
    ax.legend()
    ax.grid(alpha=0.3)
    save(fig, folder, "event_time.png", fake)


def own_factor_chart(runs, published, folder, fake):
    fig, axes = plt.subplots(len(runs), 1, figsize=(8, 3.5 * len(runs)), sharex=True)
    axes = np.atleast_1d(axes)
    for ax, (name, run) in zip(axes, runs.items()):
        ax.plot((1 + run["gross"].fillna(0)).cumprod(), label="my version")
        if published.get(name) is not None:
            label, series = published[name]
            ax.plot((1 + series.reindex(run.index).fillna(0)).cumprod(), label=label)
        ax.axhline(1, color="k", linewidth=0.8)
        ax.set_title(f"{name}, growth of 1 before costs")
        ax.legend()
        ax.grid(alpha=0.3)
    save(fig, folder, "own_factors.png", fake)
