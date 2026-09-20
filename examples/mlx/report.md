# ASX:MLX — model analysis

**As of 2026-09-20 · Base case · AUD**

**Evidence status:** Illustrative sensitivity; valuation evidence remains incomplete.

The selected case produces **0.7871 AUD/share**. This is a model result, not an investment recommendation.

**[Open the detailed Excel model](model.xlsx)** — historical evidence, editable assumptions, operating schedules, equity bridge, charts and live sensitivities.

Excel recalculated and independently checked on 2026-09-20T04:51:57.244457+00:00. This memo describes snapshot `excel-c249c7fc763c7141`; later workbook edits require `invest excel-sync` to create a new report.

## Scenario results

All three cases were recalculated in the workbook. Amounts below are in millions except per-share values.

| Case | Enterprise value | Equity value | Per share | Minimum illustrative cash |
|---|---:|---:|---:|---:|
| Bear | 24.47 | 395.19 | 0.4458 | 374.00 |
| Base | 326.99 | 697.70 | 0.7871 | 374.00 |
| Bull | 856.81 | 1,227.52 | 1.3849 | 374.00 |

The workbook opens in the selected case. Its selector updates the detailed operating model, valuation, charts and sensitivity matrix.

## What drives the result

- Explicit forecast: 2027–2031; discount rate 10.0%.
- Ownership applied to operating cash flows: 50.0%, using the declared whole operation basis.
- Equity bridge: discounted attributable cash flows + 374.00m cash + 0.00m other assets − 3.29m debt.
- Corporate costs and explicit residual value are company-attributable. The finite-life model has no terminal perpetuity.
- The cash path excludes financing, dividends and debt maturities; it is not a complete liquidity or three-statement forecast.

## Selected forecast

Amounts in millions of model currency.

| Year | Operating free cash flow | Attributable cash flow | Present value | Illustrative cash |
|---|---:|---:|---:|---:|
| 2027 | 193.38 | 94.45 | 85.86 | 468.45 |
| 2028 | 193.38 | 94.45 | 78.06 | 562.90 |
| 2029 | 193.38 | 94.45 | 70.96 | 657.34 |
| 2030 | 193.38 | 94.45 | 64.51 | 751.79 |
| 2031 | 93.38 | 44.45 | 27.60 | 796.24 |

## Sensitivity

Base-case driver × discount rate; per-share results read from recalculated Excel.

| Driver multiplier | Discount rate | Per share |
|---:|---:|---:|
| 0.8× | 8.0% | 0.5784 |
| 0.8× | 10.0% | 0.5717 |
| 0.8× | 12.0% | 0.5655 |
| 1.0× | 8.0% | 0.8053 |
| 1.0× | 10.0% | 0.7871 |
| 1.0× | 12.0% | 0.7703 |
| 1.2× | 8.0% | 1.0322 |
| 1.2× | 10.0% | 1.0026 |
| 1.2× | 12.0% | 0.9752 |

## Evidence and limitations

- [Company source 1](https://www.metalsx.com.au/wp-content/uploads/2026/03/MLX-Annual-Report-31-December-2025.pdf#page=24); dates, physical pages, units and reporting bases are recorded in the workbook's Historical sheet.
- [Company source 2](https://www.metalsx.com.au/wp-content/uploads/2026/03/MLX-Annual-Report-31-December-2025.pdf#page=25); dates, physical pages, units and reporting bases are recorded in the workbook's Historical sheet.
- [Company source 3](https://www.metalsx.com.au/wp-content/uploads/2026/03/MLX-Annual-Report-31-December-2025.pdf#page=26); dates, physical pages, units and reporting bases are recorded in the workbook's Historical sheet.
- [Company source 4](https://www.metalsx.com.au/wp-content/uploads/2026/03/MLX-Annual-Report-31-December-2025.pdf#page=60); dates, physical pages, units and reporting bases are recorded in the workbook's Historical sheet.
- [Company source 5](https://www.metalsx.com.au/wp-content/uploads/2026/03/MLX-Annual-Report-31-December-2025.pdf#page=62); dates, physical pages, units and reporting bases are recorded in the workbook's Historical sheet.
- [Company source 6](https://www.metalsx.com.au/wp-content/uploads/2026/03/MLX-Annual-Report-31-December-2025.pdf#page=9); dates, physical pages, units and reporting bases are recorded in the workbook's Historical sheet.
- [Company source 7](https://www.metalsx.com.au/wp-content/uploads/2026/07/02_MLX_Quarterly-Report_30-June-2026_Final.pdf#page=2); dates, physical pages, units and reporting bases are recorded in the workbook's Historical sheet.
- [Company source 8](https://www.metalsx.com.au/wp-content/uploads/2026/07/02_MLX_Quarterly-Report_30-June-2026_Final.pdf#page=3); dates, physical pages, units and reporting bases are recorded in the workbook's Historical sheet.
- [Company source 9](https://www.metalsx.com.au/wp-content/uploads/2026/07/02_MLX_Quarterly-Report_30-June-2026_Final.pdf#page=8); dates, physical pages, units and reporting bases are recorded in the workbook's Historical sheet.
- [Company source 10](https://www.metalsx.com.au/wp-content/uploads/2026/07/02_MLX_Quarterly-Report_30-June-2026_Final.pdf#page=9); dates, physical pages, units and reporting bases are recorded in the workbook's Historical sheet.
- ILLUSTRATIVE IMPUTED-REVENUE SENSITIVITY ONLY. This is not an actionable fair-value estimate or an investment recommendation.
- Production is used solely as the company-style imputed-revenue proxy (100% produced tin sold/paid); it is NOT reported payable sales. The workbook labels it production_tonnes_proxy. Realized payable sales, inventory, settlement timing and revenue must replace this proxy before valuation.
- The baseline price AUD63,760/t is the reported trailing-12-month LME-imputed price, NOT realized tin sales price. Scenario price and volume levels are analyst stress assumptions, not company guidance.
- Unit cost combines reported trailing-12-month C1 AUD19,349/t and imputed sales/marketing AUD8,089/t. Marketing includes royalties and payable-tin deductions, so separate royalty_rate=0 prevents duplicate deductions. Price-linked marketing behavior is not separately modelled and could materially affect sensitivity.
- Finite horizons 3/5/7 years are illustrative assumptions, not reserve-supported mine life. The quarterly report said an updated life-of-mine plan and Ore Reserve were expected in Q3 2026; those updates have not been verified. No perpetuity or residual value is included.
- Cash AUD374m is as at June 30 2026; debt AUD3.285m and issued shares886,391,538 are as at December31 2025. These stale mixed-date balances need updated half-year/ASX checks. Issued shares are a proxy, NOT a verified current fully diluted denominator.
- Closure is an explicit assumed AUD100m whole-operation nominal final-year payment. The reported AUD33.035m group rehabilitation provision is a present-value accounting figure, not this cash-payment estimate; actual scope/timing and other closure sites remain unmodelled.
- Capex annualizes June-quarter whole-operation AUD23.4m to AUD93.6m each model year, including both sustaining and project spend. This is a scenario assumption, not guidance. No additional AISC deduction is made.
- Annual corporate costs annualize group June-quarter AUD0.56m to AUD2.24m, deducted once after 50% attribution. Other investments/residual assets are set to zero only to exclude them from this limited sensitivity, not because they have zero economic value.
- Tax rate30% is an analyst simplifying assumption; depreciation is assumed zero and no loss carryforwards, corporate tax shields or closure deductions are modelled. No forecast working-capital changes are assumed; this is not verified operational guidance.
- Annual row labels2027 onward denote period-end annualized flows one/two/etc years from the valuation date, not an audited fiscal calendar projection. No remaining2026 stub cash flow is forecast. Forecast years are constant run-rate proxies.
- No verified current share quote is supplied. Reverse valuation and price/upside comparisons are unavailable. No actual user portfolio is used.
- Historical statement summaries now include FY2025 and FY2024 as reported in the 2025 annual report. This is a selected comparative history, not a full three-year normalization or a linked three-statement forecast. Group consolidated actuals must not be compared directly with unscaled whole-operation model rows.
- Current reference quote unavailable: no upside/downside versus market or reverse-valuation conclusion is presented.

## Changes and audit trail

No input overrides versus this workbook's recorded baseline.

Snapshot workbook SHA-256: `094641e69087c127b01b8936fbc77aec8a52a7863158a6b26f4a4ae97f41f60c`.

[Accepted input and provenance snapshot](inputs.json) · [Calculation results and validation](model.json)
