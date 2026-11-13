# Results

212 published predictors, monthly long-short returns 1926-01 to 2025-12.

## How many factors pass each bar

| period | factors tested | t > 1.96 | t > 3.0 | Bonferroni | Benjamini-Hochberg | Benjamini-Yekutieli |
|---|---|---|---|---|---|---|
| in original sample | 208 | 183 | 120 | 80 | 179 | 138 |
| after publication | 209 | 54 | 24 | 9 | 33 | 9 |
| full history | 212 | 173 | 134 | 96 | 166 | 149 |

Benjamini-Hochberg and Benjamini-Yekutieli control the false discovery rate at 5%. Bonferroni controls the chance of any false positive at 5%.

## Decay after the sample and after publication

| period | change in monthly return | t | change as share of in-sample mean |
|---|---|---|---|
| after sample end, before publication | -0.0023 | -3.6874 | -0.3503 |
| after publication | -0.0037 | -6.7190 | -0.5556 |

Average in-sample return: 0.670% a month. 138,686 factor-months, factor fixed effects, standard errors clustered by month. Across the 205 factors with both periods, the average post-publication return is 45% of the average in-sample return.

## Beyond Fama-French

| factors tested | raw mean t > 1.96 | alpha t > 1.96 | alpha t > 3.0 | median R2 |
|---|---|---|---|---|
| 212 | 169 | 161 | 120 | 0.320 |

Each factor is regressed on MKT, SMB, HML, RMW, CMA and UMD over its full history.

## Factors built from prices

503 stocks, top and bottom 20%, equal weights, 10 bp cost per unit of turnover.

| factor | mean monthly return, gross | t, gross | Sharpe, gross | mean monthly return, net | t, net | Sharpe, net | avg monthly turnover | months |
|---|---|---|---|---|---|---|---|---|
| momentum (12-2) | 0.0000 | 0.0151 | 0.0030 | -0.0009 | -0.2812 | -0.0553 | 0.9505 | 310 |
| low volatility (1 month) | -0.0107 | -2.7005 | -0.5213 | -0.0126 | -3.1631 | -0.6106 | 1.8317 | 322 |

| factor | published series | months | correlation | beta on published | monthly alpha vs published | alpha t |
|---|---|---|---|---|---|---|
| momentum (12-2) | French UMD | 308 | 0.9269 | 1.1103 | -0.0020 | -1.6686 |
| momentum (12-2) | OSAP Mom12m | 299 | 0.6879 | 0.4681 | -0.0047 | -2.0377 |
| low volatility (1 month) | OSAP RealizedVol | 311 | 0.8965 | 0.7055 | -0.0126 | -7.0668 |
| low volatility (1 month) | OSAP IdioVol3F | 311 | 0.8590 | 0.7805 | -0.0143 | -6.9145 |
