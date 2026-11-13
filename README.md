# factor-zoo

Hundreds of papers claim to have found a stock characteristic that predicts returns. I wanted to see how many of them still work once you hold them to a stricter test, and what happened to them after they were published.

I used the Open Source Asset Pricing data from Chen and Zimmermann, which has monthly long-short returns for 212 published predictors going back to 1926, plus the Fama-French factors from Ken French's website.

## What I found

| | Tested | t > 1.96 | t > 3 |
|---|---|---|---|
| Inside the original paper's sample | 208 | 183 | 120 |
| After publication | 209 | 54 | 24 |

Most predictors look strong in the data they were found in and much weaker afterwards. Part of that is just that the samples after publication are shorter, so I also ran a pooled regression like McLean and Pontiff (2016). Returns fall about 35% after the paper's sample ends and about 56% after publication (t = -6.7). They got 26% and 58% on 97 predictors, so my numbers line up with theirs on a bigger set.

161 of the 212 still have a significant alpha after controlling for the Fama-French five factors plus momentum, so most of them aren't just old factors in disguise.

I also rebuilt momentum and low volatility myself from S&P 500 prices. They track the published versions closely (correlations of 0.93 and 0.90), but my low volatility factor loses about 1% a month. That's survivorship bias. I used today's S&P 500 members, so every volatile stock in my sample is one that survived and grew, and shorting those loses money in hindsight. Fixing it needs a list of who was actually in the index at each date, which is the next thing I want to add.

## Running it

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/get_data.py
python src/run_all.py
```

`get_data.py` downloads everything (the stock prices take a while). The results go to `results/summary.md` and the charts to `results/figures/`.

Before trusting the code on real data I checked it on fake data with known answers planted in it, including 80 factors that are pure noise:

```
python tests/make_fake_data.py
python src/run_all.py --fake
python tests/check_fake.py
```

## Files

- `src/get_data.py` downloads the data
- `src/zoo_tests.py` has the significance counts, the decay regression and the alpha regressions
- `src/own_factors.py` builds momentum and low volatility from prices
- `src/run_all.py` runs everything and writes `results/`
- `DATA_NOTES.md` has more detail on the data and the choices I made
