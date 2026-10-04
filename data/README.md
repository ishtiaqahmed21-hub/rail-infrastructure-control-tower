# Data contract and provenance

Raw ORR snapshots are small official published tables, frozen on 2026-09-28. They can be redistributed under OGL v3.0 with attribution, subject to excluded third-party content/logos. Contains Office of Rail and Road data, sourced from Network Rail, licensed under the Open Government Licence v3.0. Infrastructure also credits Transport for London and Amey Infrastructure Wales. Code MIT licensing does not relicense source data.

[ORR reuse terms](https://www.orr.gov.uk/terms-and-conditions) · [OGL](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)

`manifest.json` gives exact URLs, SHA256, byte sizes and retrieval date. To refresh, download those URLs to the same raw filenames, preserve an old manifest, rerun the pipeline and review schema/count changes before accepting a new snapshot. Table 3181a exports are client-side; HTML is the actual retrieval resource.

| File | Shape | Contract |
|---|---|---|
| raw/orr_3181a.html | 96 × 11 | Period + five regional periodic rates + five moving annual rates; [z] missing |
| raw/orr_6320.ods | 79 × 7 substantive fields | Nation, date label, five route/track km fields; [x] missing, [b] structural break |
| processed/ledger.csv | 496 rows (16 WBS × 31 weekly snapshots) | Unique (wbs,week); nondecreasing actual quantities, actual<=scope; costs GBP |
| processed/status.csv | 16 WBS rows | Single status date; baseline/actual fractions, dated earned-schedule diagnostic |
| processed/risks.csv | 6 risks | Probability [0,1], monetary impact GBP, exposure, owner, mitigation and due date |

**OBSERVED:** published ORR context. **ASSUMPTION:** scenario scope, baseline, rates, recovery premium and risk parameters. **SIMULATED:** all project ledger inputs. **DERIVED:** EVM, risk exposure and forecasts computed from those inputs; origin remains SIMULATED. Source public observations must never be represented as construction records.

ORR rate units: delay-minutes per 1,000 train-miles, not minutes per train. Regions cannot be summed or averaged into a national rate without train-mile weights. Railway periods have 13 observations per full financial year, not 12 months. Infrastructure route-km differs from track-km; breaks in April 2005, 2007, 2017 and 2024 limit trend comparisons; HS1, Isle of Wight and Heathrow Link excluded.
