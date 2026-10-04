# Power BI / Tableau implementation specification

This is a six-page analytical specification accompanied by a working local HTML prototype and labeled PNG overview. It does not claim to be a native BI workbook.

## Data model and refresh

FactProgress grain WBS × status week; DimWBS unique WBS with section, discipline, unit, approved scope and baseline dates; DimDate weekly calendar; FactRisk one row per risk (snapshot date required when historizing); FactForecast one WBS × scenario × status date. Load processed CSV outputs. Relate dimensions one-to-many, single-direction; do not join risk rows directly to progress (fanout). Store budget once per WBS or calculate only selected snapshot; never sum cumulative progress across dates. FactORR is disconnected context with period labels and region; it must not filter project performance. All project pages show SIMULATED banner and status date. Refresh weekly after approval; preserve baseline versions and refresh audit log. Operational context follows ORR publications and revision logs.

## Six pages and interactions

1. **Executive Control Tower:** BAC, EV, AC, CPI, SPI, EAC, VAC cards; PV/EV/AC time series; status date and provenance prominent. Selecting section filters scope, not ORR. Drill through to section detail.
2. **Section Performance:** CPI/SPI comparison, earned physical quantities by discipline with native units, budget-weighted scope progress and forecast availability. Drill to WBS and source rows. Never add stations to miles.
3. **Schedule & Milestones:** baseline/earned bars, dated finish table, complete/open/overdue counts, earned-schedule diagnostic and stalled package list. Completed milestones preserve actual completion dates.
4. **Cost & Earned Value:** budget/spend/EAC bridge; outstanding commitments separate; CV/SV in GBP, CPI/SPI unitless, VAC and EAC assumption selector. Baseline-productivity versus CPI-persistence scenarios shown explicitly.
5. **Risk Register / Heatmap:** probability × ordinal impact grid, expected monetary exposure by owner, full risk table with mitigation and due dates; drill to actions. Risk exposure is not automatically added to EAC.
6. **Forecast & Recovery Scenarios:** baseline/current/recovery finish by WBS; whole-project forecast blocked if any incomplete package stalls; productivity multiplier and premium sensitivity; show forecastable latest date separately. Separate collapsible OBSERVED ORR context chart.

## Complete KPI dictionary

All project sources below are SIMULATED input or DERIVED with SIMULATED origin. Thresholds are portfolio assumptions, not standards. Refresh is weekly unless specified.

| KPI / definition | Formula | Data source | Owner | Refresh | Threshold |
|---|---|---|---|---|---|
| BAC approved scope budget | sum(unique WBS budget) at status | status.csv | Project controls manager | Weekly / baseline change | Baseline only; changes require approval |
| Planned physical progress | planned_quantity/scope_quantity, by native unit | status.csv | Planning engineer | Weekly | Reference baseline |
| Actual earned progress | actual_quantity/scope_quantity | status.csv | Construction manager | Weekly | Actual/planned >=.95 green, >=.85 amber, else red |
| Weighted programme progress | EV/BAC | status.csv | Controls manager | Weekly | Compare with PV/BAC using SPI thresholds |
| PV budgeted planned work | sum(budget*planned_fraction) | status.csv | Planner | Weekly | Reference baseline |
| EV budgeted earned work | sum(budget*actual_fraction) | status.csv | Quantity surveyor | Weekly | Compare with PV |
| AC cumulative expenditure | sum(actual_cost) at date | status.csv | Cost engineer | Weekly | Compare with EV |
| CV earned-value cost variance | EV-AC, GBP | cost.py | Cost engineer | Weekly | >=0 green; negative with CPI>=.85 amber; else red |
| SV earned-value schedule variance | EV-PV, GBP (not days) | kpi_engine.py | Planner | Weekly | >=0 green; negative with SPI>=.85 amber; else red |
| CPI cost efficiency | EV/AC; undefined AC<=0 | cost.py | Cost engineer | Weekly | >=.95 green; >=.85 amber; otherwise red; undefined gray |
| SPI schedule efficiency | EV/PV; undefined PV<=0 | kpi_engine.py | Planner | Weekly | >=.95 green; >=.85 amber; otherwise red; undefined gray |
| Outstanding commitments | sum(unspent committed obligations) | status.csv | Commercial manager | Weekly | Investigate if AC+commitments>BAC |
| Management EAC | max(AC+(BAC-EV)/CPI, AC+unpaid commitments) | cost.py | Controls manager | Weekly | <=BAC green; <=1.10*BAC amber; else red |
| VAC forecast cost variance | BAC-EAC | cost.py | Sponsor | Weekly | >=0 green; >=-.10*BAC amber; else red |
| Completed milestones | count actual_fraction>=1 | milestones.csv | Planner | Weekly | Overdue count zero green; any overdue amber; >14d red |
| Milestone overdue days | max(status-baseline finish,0) if incomplete | milestones.csv | Planner | Weekly | 0 green; <=14 amber; >14 red |
| Earned schedule diagnostic | max(status week-(start+earned fraction*duration),0)*7 | status.csv | Planner | Weekly | <=7 green; <=21 amber; >21 red; linear baseline only |
| Forecast finish/current | status+remaining/last4-week rate; completed actual finish | forecast.csv | Planner | Weekly | <=baseline green; <=baseline+21d amber; later red; stalled gray |
| Recovery finish | status+remaining/(1.25*recent rate) | forecast.csv | Construction manager | Weekly | Scenario only; same delay thresholds |
| Recovery EAC | AC+(EAC-AC)*1.08 | results.json | Cost engineer | Weekly | Assumption; require funding approval |
| Risk probability | assigned probability [0,1] | risks.csv | Risk owner | Weekly | Input assumption |
| Risk monetary exposure | probability*impact_gbp | risks.csv | Risk manager | Weekly | >GBP3m escalate; not a reserve estimate |
| Ordinal risk score | ceil(5*probability)*impact_band | risks.csv | Risk manager | Weekly | >=15 red; >=8 amber; else green |
| Mitigation overdue | status_date>due_date and open | risks.csv | Accountable owner | Weekly | Any overdue escalate; no claim of closure without evidence |
| Track / electrification complete | sum actual quantities filtered discipline | status.csv | Engineering lead | Weekly | Native route-miles; compare same scope planned |
| Stations / signaling complete | sum completed integer units | status.csv | Engineering lead | Weekly | Native count; compare approved package milestones |
| ORR regional delay rate | published delay minutes/1,000 train-miles | orr_operations.csv | Operations analyst | ORR periodic release | OBSERVED contextual; no fictional target |

## Acceptance checks

One selected status date; cumulative budgets/spend not summed across time; zero denominators displayed N/A; WBS weighted EVM reconciles to programme totals; no physical-unit mixing; commitments excluded from AC; forecast missingness visible; risk monetary/ordinal measures distinct; ORR source and provisional/revision note retained. Screen reader labels, high-contrast RAG text plus colour, visible units and hover formula/tooltips required. Native BI publication would additionally require data-owner signoff and access testing.
