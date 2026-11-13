# Data notes

## Published factor returns

The factor returns come from the Open Source Asset Pricing project (Chen and Zimmermann). `get_data.py` downloads `PredictorPortsFull.parquet` from their Hugging Face repo and tries the releases in `src/config.py`, newest first. My run used the October 2026 release, which has about 1.24 million rows.

I only use the long-short portfolio (`port == "LS"`) for each predictor. The returns are stored in percent, so `load.py` checks the typical size and divides by 100. On my run a typical monthly move was 1.65%, so that worked as expected.

Every factor is already signed so that the original paper's prediction is a positive return.

`SignalDoc.csv` gives each predictor's sample years and publication year. All 212 predictors matched up with return data.

## Fama-French factors

These come from Ken French's data library. `src/french.py` reads the monthly table and converts it from percent to decimals. My copy runs from July 1963 to September 2026.

## Stock prices

The momentum and low volatility factors I built use today's S&P 500 members, downloaded from Yahoo Finance. All 503 tickers came back on my run, from 2000 to November 2026.

Using today's members means survivorship bias. Any stock that was volatile in the past and is in the index now is one that survived and grew, which is why my low volatility factor loses money. A list of who was in the index at each date would fix this.

Yahoo prices are adjusted for splits and dividends as of today.

## Choices I made

- Volatility uses a 21-day window, which matches the one-month realized volatility in Ang et al. (2006). A 12-month window is the more common definition of low volatility.
- Portfolios are equal weighted and split into fifths. The published versions use different breakpoints and weights, which is part of why the correlations aren't higher.
- Periods are assigned by calendar year from the documentation, so months where a working paper was already circulating count as "before publication".
