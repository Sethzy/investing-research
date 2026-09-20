# DEMO:MINE — model analysis

**As of 2026-09-20 · Base case · AUD**

**Evidence status:** Synthetic worked example.

The selected case produces **3.6306 AUD/share**. This is a model result, not an investment recommendation.

**[Open the detailed Excel model](model.xlsx)** — historical evidence, editable assumptions, operating schedules, equity bridge, charts and live sensitivities.

Excel recalculated and independently checked on 2026-09-20T03:40:42.699172+00:00. This memo describes snapshot `excel-0713b67e6b8734d4`; later workbook edits require `invest excel-sync` to create a new report.

## Scenario results

All three cases were recalculated in the workbook. Amounts below are in millions except per-share values.

| Case | Enterprise value | Equity value | Per share | Minimum illustrative cash |
|---|---:|---:|---:|---:|
| Bear | 0.00 | 0.00 | 2.3289 | 0.00 |
| Base | 0.00 | 0.00 | 3.6306 | 0.00 |
| Bull | 0.00 | 0.00 | 4.9322 | 0.00 |

The workbook opens in the selected case. Its selector updates the detailed operating model, valuation, charts and sensitivity matrix.

## What drives the result

- Explicit forecast: 2027–2028; discount rate 10.0%.
- Ownership applied to operating cash flows: 50.0%, using the declared whole operation basis.
- Equity bridge: discounted attributable cash flows + 0.00m cash + 0.00m other assets − 0.00m debt.
- Corporate costs and explicit residual value are company-attributable. The finite-life model has no terminal perpetuity.
- The cash path excludes financing, dividends and debt maturities; it is not a complete liquidity or three-statement forecast.

## Selected forecast

Amounts in millions of model currency.

| Year | Operating free cash flow | Attributable cash flow | Present value | Illustrative cash |
|---|---:|---:|---:|---:|
| 2027 | 0.00 | 0.00 | 0.00 | 0.00 |
| 2028 | 0.00 | 0.00 | 0.00 | 0.00 |

## Sensitivity

Base-case driver × discount rate; per-share results read from recalculated Excel.

| Driver multiplier | Discount rate | Per share |
|---:|---:|---:|
| 0.8× | 8.0% | 2.3689 |
| 0.8× | 10.0% | 2.3289 |
| 0.8× | 12.0% | 2.2908 |
| 1.0× | 8.0% | 3.7064 |
| 1.0× | 10.0% | 3.6306 |
| 1.0× | 12.0% | 3.5583 |
| 1.2× | 8.0% | 5.0438 |
| 1.2× | 10.0% | 4.9322 |
| 1.2× | 12.0% | 4.8258 |

## Evidence and limitations


## Changes and audit trail

No input overrides versus this workbook's recorded baseline.

Snapshot workbook SHA-256: `2656f3cb51f5c196b1dd2f239cab7e40251aa65c997092f1d5b569f5695c74a9`.

[Accepted input and provenance snapshot](inputs.json) · [Calculation results and validation](model.json)
