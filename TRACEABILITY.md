# Finding-to-action traceability

| ID | Source → transformation → output | Finding / decision |
|---|---|---|
| RAIL-01 | SIMULATED generator → status_snapshot → earned_value/cost_summary → sections.csv and figures/02_sections.png | Identify lowest section CPI/SPI; prioritize possession and supply actions in designed S3 case |
| RAIL-02 | SIMULATED quantity history → four-interval production → forecast.csv and figures/06_forecast.png | Stalled packages require production plan; no unsupported overall finish date |
| RAIL-03 | SIMULATED probabilities/impacts → assess_risks → risks.csv and figures/05_risk.png | R01/R02 high priority; accountable owners and dated actions |
| RAIL-04 | OBSERVED ORR HTML → strict schema numeric parsing → orr_operations.csv and figures/07_orr_context.png | Illustrate regional operating context without linking causally to fictional work |
| RAIL-05 | SIMULATED costs → EAC and commitment floor → results.json and figures/04_cost.png | Compare budget, estimate, and recovery cost; no double count of commitments |

Machine-readable metrics: reports/results.json. Recreate with python -m src.pipeline. Every recommendation is scenario evidence; real decisions require current field records, procurement evidence, baseline approval and feasibility review.
