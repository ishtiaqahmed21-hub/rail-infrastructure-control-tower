"""Build deterministic project controls, observed context, reports and dashboard assets."""

from pathlib import Path
import hashlib
import json
import shutil
import numpy as np
import pandas as pd
import yaml
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from .kpi_engine import earned_value, rag
from .cost import cost_summary
from .schedule import status_snapshot, milestone_status, earned_schedule_days
from .risk import assess_risks
from .forecast import forecast_packages, progress_scenarios
from .data_sources import load_operations, load_infrastructure
from .artifact_utils import write_report

ROOT = Path(__file__).resolve().parents[1]


def generate_ledger(config):
    """Seeded quantity/cost ledger; simulation parameters are explicit assumptions."""
    rng = np.random.default_rng(config["seed"])
    rows = []
    start = pd.Timestamp(config["start_date"])
    disciplines = [
        ("Track", "route-mile", 0, 40, 1.6e6),
        ("Electrification", "route-mile", 8, 47, 1.1e6),
        ("Stations", "station", 4, 44, 12e6),
        ("Signaling", "installation", 15, 52, 2e6),
    ]
    for i, miles in enumerate([18, 16, 20, 14]):
        section = f"S{i+1}"
        for j, (name, unit, begin, end, unit_cost) in enumerate(disciplines):
            scope = miles if j < 2 else (2 if j == 2 else 4)
            budget = scope * unit_cost
            pace = [0.99, 0.94, 0.74, 0.91][i] * (0.96 if j == 1 else 1)
            cost_factor = [1.02, 1.07, 1.22, 1.10][i]
            actual = 0.0
            for week in range(config["status_week"] + 1):
                planned = scope * np.clip((week - begin) / (end - begin), 0, 1)
                if week > begin:
                    actual = min(
                        scope,
                        actual + scope / (end - begin) * pace * rng.uniform(0.9, 1.1),
                    )
                # Stations/signaling are earned only on completed physical units.
                earned_quantity = np.floor(actual) if j >= 2 else actual
                frac = earned_quantity / scope
                ac = budget * frac * cost_factor + budget * 0.01 * np.clip(
                    (week - begin) / (end - begin), 0, 1
                )
                outstanding = budget * (1 - frac) * 0.65
                rows.append(
                    dict(
                        wbs=f"{section}-{j+1}",
                        section=section,
                        discipline=name,
                        unit=unit,
                        week=week,
                        date=(start + pd.Timedelta(weeks=week)).date().isoformat(),
                        start_week=begin,
                        finish_week=end,
                        baseline_finish=(start + pd.Timedelta(weeks=end))
                        .date()
                        .isoformat(),
                        scope_quantity=scope,
                        planned_quantity=planned,
                        actual_quantity=earned_quantity,
                        budget=budget,
                        actual_cost=ac,
                        outstanding_commitments=outstanding,
                        evidence_type="SIMULATED",
                    )
                )
    return pd.DataFrame(rows)


def make_risks(status_date):
    """Fictional named accountable roles; costs and probabilities are assumptions."""
    items = [
        (
            "R01",
            "S3",
            "Possession access restricted",
            0.65,
            8e6,
            5,
            "Construction manager",
            "Agree alternative possession windows",
            14,
        ),
        (
            "R02",
            "S3",
            "Electrification supply lead time",
            0.55,
            5e6,
            4,
            "Supply chain manager",
            "Reserve approved alternate supplier",
            21,
        ),
        (
            "R03",
            "S2",
            "Station interface rework",
            0.35,
            3e6,
            3,
            "Design manager",
            "Close design interface reviews",
            28,
        ),
        (
            "R04",
            "ALL",
            "Safety assurance approval delay",
            0.3,
            7e6,
            5,
            "Assurance manager",
            "Independent assurance readiness review",
            35,
        ),
        (
            "R05",
            "S4",
            "Ground conditions at station",
            0.2,
            4e6,
            4,
            "Geotechnical lead",
            "Targeted ground investigation",
            7,
        ),
        (
            "R06",
            "ALL",
            "Signaling integration test failure",
            0.4,
            6e6,
            4,
            "Systems manager",
            "Early test rig integration",
            42,
        ),
    ]
    cols = [
        "risk_id",
        "section",
        "description",
        "probability",
        "impact_gbp",
        "impact_band",
        "owner",
        "mitigation",
        "due_offset",
    ]
    frame = pd.DataFrame(items, columns=cols)
    frame["due_date"] = (
        pd.Timestamp(status_date) + pd.to_timedelta(frame.pop("due_offset"), unit="D")
    ).dt.date
    frame["evidence_type"] = "SIMULATED"
    return assess_risks(frame)


def plot_assets(ledger, snapshot, risks, forecasts, operations, metrics):
    """Produce six labeled dashboard panel graphics and a composed prototype."""
    plt.rcParams.update(
        {
            "figure.facecolor": "#f4f7fa",
            "axes.facecolor": "white",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "font.size": 10,
        }
    )
    series = pd.DataFrame(
        [
            {"week": w, **earned_value(status_snapshot(ledger, w))}
            for w in sorted(ledger.week.unique())
        ]
    )
    sections = pd.DataFrame(
        [{"section": s, **earned_value(g)} for s, g in snapshot.groupby("section")]
    )

    def save(fig, name, title):
        fig.suptitle(
            title + "\nDERIVED FROM SIMULATED PROJECT RECORDS",
            fontsize=14,
            fontweight="bold",
        )
        fig.tight_layout(rect=(0, 0, 1, 0.91))
        fig.savefig(ROOT / "figures" / name, dpi=160)
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(series.week, series.PV / 1e6, label="PV")
    ax.plot(series.week, series.EV / 1e6, label="EV")
    ax.plot(series.week, series.AC / 1e6, label="AC")
    ax.set(xlabel="Reporting week", ylabel="GBP million")
    ax.legend()
    save(fig, "01_executive.png", "Earned value control tower")
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(4)
    ax.bar(x - 0.18, sections.CPI, 0.36, label="CPI")
    ax.bar(x + 0.18, sections.SPI, 0.36, label="SPI")
    ax.set_xticks(x, sections.section)
    ax.axhline(0.95, color="#e68a00", ls="--")
    ax.set(ylabel="Index")
    ax.legend()
    save(fig, "02_sections.png", "Section cost and schedule efficiency")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(snapshot.wbs, snapshot.planned_fraction, label="Planned", color="#bdcbd4")
    ax.barh(
        snapshot.wbs,
        snapshot.actual_fraction,
        label="Earned",
        height=0.45,
        color="#007f82",
    )
    ax.set(xlabel="Physical scope fraction")
    ax.legend()
    save(fig, "03_schedule.png", "Work-package physical milestones")
    fig, ax = plt.subplots(figsize=(10, 5))
    keys = ["BAC", "AC", "outstanding_commitments", "management_EAC"]
    ax.bar(
        ["Budget", "Spent", "Unpaid commitments", "Forecast EAC"],
        [metrics[k] / 1e6 for k in keys],
        color=["#12344a", "#007f82", "#bdcbd4", "#d5654c"],
    )
    ax.set(ylabel="GBP million")
    save(fig, "04_cost.png", "Cost outlook; commitments are not added twice")
    fig, ax = plt.subplots(figsize=(10, 5))
    heat = np.outer(np.arange(1, 6), np.arange(1, 6))
    ax.imshow(
        heat,
        origin="lower",
        cmap="YlOrRd",
        extent=(0.5, 5.5, 0.5, 5.5),
        vmin=1,
        vmax=25,
        aspect="auto",
    )
    for (x, y), g in risks.groupby(["impact_band", "probability_band"]):
        ax.text(
            x,
            y,
            ", ".join(g.risk_id),
            ha="center",
            bbox=dict(facecolor="white", alpha=0.85, edgecolor="none"),
        )
    ax.set(
        xticks=range(1, 6),
        yticks=range(1, 6),
        xlabel="Ordinal impact band",
        ylabel="Probability band",
    )
    save(fig, "05_risk.png", "Risk heatmap; expected monetary exposure separate")
    fig, ax = plt.subplots(figsize=(10, 6))
    base = pd.to_datetime(forecasts.baseline_finish)
    current = pd.to_datetime(forecasts.current_finish)
    recovery = pd.to_datetime(forecasts.recovery_finish)
    ax.scatter(
        (current - base).dt.days, forecasts.wbs, label="Current", color="#d5654c"
    )
    ax.scatter(
        (recovery - base).dt.days,
        forecasts.wbs,
        label="Recovery assumption",
        color="#007f82",
    )
    ax.axvline(0, color="gray")
    ax.set(xlabel="Forecast days versus baseline finish")
    ax.legend()
    save(fig, "06_forecast.png", "Completion scenario comparison")
    fig, ax = plt.subplots(figsize=(10, 5))
    for c in operations.columns[1:6]:
        ax.plot(
            np.arange(len(operations)), operations[c], label=c.replace("_periodic", "")
        )
    ax.set(
        xlabel="Railway period sequence since 2019/20 P01",
        ylabel="Delay minutes / 1,000 train-miles",
    )
    ax.legend(fontsize=8)
    fig.suptitle("OBSERVED ORR regional rail context — separate from fictional project")
    fig.tight_layout()
    fig.savefig(ROOT / "figures/07_orr_context.png", dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    for ax, f in zip(axes.flat, sorted((ROOT / "figures").glob("0[1-6]*.png"))):
        ax.imshow(plt.imread(f))
        ax.axis("off")
    fig.suptitle(
        "FICTIONAL MERIDIAN RAIL | SIMULATED CONTROL TOWER PROTOTYPE",
        fontweight="bold",
        fontsize=18,
    )
    fig.tight_layout()
    fig.savefig(ROOT / "dashboard/dashboard_prototype.png", dpi=140)
    plt.close(fig)
    return series, sections


def main():
    config = yaml.safe_load((ROOT / "config/project_config.yaml").read_text())
    ledger = generate_ledger(config)
    snapshot = status_snapshot(ledger, config["status_week"])
    metrics = cost_summary(snapshot)
    metrics["status_date"] = snapshot.date.iloc[0]
    metrics["SPI_RAG"] = rag(metrics["SPI"])
    metrics["CPI_RAG"] = rag(metrics["CPI"])
    metrics["physical_progress_budget_weighted"] = metrics["EV"] / metrics["BAC"]
    metrics["route_miles_earned"] = float(
        snapshot.loc[snapshot.discipline == "Track", "actual_quantity"].sum()
    )
    risks = make_risks(metrics["status_date"])
    forecasts = forecast_packages(
        ledger, config["status_week"], config["recovery_productivity_multiplier"]
    )
    trajectories = progress_scenarios(
        ledger, config["status_week"], config["recovery_productivity_multiplier"]
    )
    trajectories.to_csv(ROOT / "data/processed/progress_scenarios.csv", index=False)
    trajectories.groupby(["scenario", "section", "week", "date"], as_index=False).agg(
        projected_ev=("projected_ev", "sum"), budget=("budget", "sum")
    ).assign(evidence_type="DERIVED", origin="SIMULATED").to_csv(
        ROOT / "data/processed/section_progress_forecast.csv", index=False
    )
    milestones = milestone_status(snapshot)
    snapshot["earned_schedule_days_behind"] = earned_schedule_days(snapshot)
    metrics["baseline_finish"] = forecasts.baseline_finish.max()
    metrics["stalled_packages"] = forecasts.loc[
        (forecasts.actual_quantity < forecasts.scope_quantity)
        & forecasts.current_finish.isna(),
        "wbs",
    ].tolist()
    metrics["latest_forecastable_finish"] = str(forecasts.current_finish.max().date())
    metrics["current_finish"] = (
        "UNAVAILABLE: stalled packages"
        if metrics["stalled_packages"]
        else str(forecasts.current_finish.max().date())
    )
    metrics["recovery_finish"] = (
        "UNAVAILABLE: stalled packages"
        if metrics["stalled_packages"]
        else str(forecasts.recovery_finish.max().date())
    )
    metrics["risk_exposure_gbp"] = float(risks.exposure_gbp.sum())
    metrics["milestones_complete"] = int(milestones.complete.sum())
    metrics["recovery_EAC"] = metrics["AC"] + (
        metrics["management_EAC"] - metrics["AC"]
    ) * (1 + config["recovery_cost_premium"])
    operations = load_operations(ROOT / "data/raw/orr_3181a.html")
    infrastructure = load_infrastructure(ROOT / "data/raw/orr_6320.ods")
    series, sections = plot_assets(
        ledger, snapshot, risks, forecasts, operations, metrics
    )
    for name, frame in [
        ("ledger", ledger),
        ("status", snapshot),
        ("risks", risks),
        ("forecast", forecasts),
        ("milestones", milestones),
        ("evm_history", series),
        ("sections", sections),
        ("orr_operations", operations),
        ("orr_infrastructure", infrastructure),
    ]:
        frame = frame.copy()
        if "evidence_type" not in frame:
            frame["evidence_type"] = "OBSERVED" if name.startswith("orr") else "DERIVED"
        frame["origin"] = "OFFICIAL ORR" if name.startswith("orr") else "SIMULATED"
        frame.to_csv(ROOT / f"data/processed/{name}.csv", index=False)
    results = {
        "evidence_type": "DERIVED",
        "origin": "SIMULATED",
        "project_metrics": metrics,
        "observed_context": {
            "operations_rows": len(operations),
            "infrastructure_rows": len(infrastructure),
            "latest_period": operations.period.iloc[-1],
            "latest_regional_delay_rates": operations.iloc[-1, 1:6].to_dict(),
        },
        "assumptions": config,
    }
    (ROOT / "reports/results.json").write_text(
        json.dumps(results, indent=2, allow_nan=False, default=str)
    )
    manifest = {"access_date": "2026-09-28", "sources": []}
    urls = {
        "orr_3181a.html": "https://dataportal.orr.gov.uk/statistics/performance/passenger-rail-performance/table-3181a-delay-minutes-per-1-000-train-miles-total-by-network-rail-region-periodic-1/",
        "orr_6320.ods": "https://dataportal.orr.gov.uk/media/1528/table-6320-infrastructure-on-the-mainline.ods",
    }
    for f in sorted((ROOT / "data/raw").iterdir()):
        manifest["sources"].append(
            {
                "file": f.name,
                "url": urls[f.name],
                "sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
                "bytes": f.stat().st_size,
                "license": "OGL v3.0",
                "origin": "OBSERVED",
            }
        )
    (ROOT / "data/manifest.json").write_text(json.dumps(manifest, indent=2))
    overview = f"DERIVED FROM SIMULATED RECORDS: At {metrics['status_date']}, the GBP {metrics['BAC']/1e6:.1f}m fictional programme has earned {metrics['physical_progress_budget_weighted']:.1%} of its budgeted scope. CPI {metrics['CPI']:.3f}, SPI {metrics['SPI']:.3f}, cost variance GBP {metrics['CV']/1e6:.2f}m and EAC GBP {metrics['management_EAC']/1e6:.2f}m. These are demonstration outputs, not real project performance."
    schedule = f"Baseline completion {metrics['baseline_finish']}; current rate extrapolation {metrics['current_finish']}; recovery {metrics['recovery_finish']}. The recovery assumes 25% more weekly production and 8% premium on remaining forecast cost, giving GBP {metrics['recovery_EAC']/1e6:.2f}m EAC. Latest forecastable package finishes {metrics['latest_forecastable_finish']}; stalled packages {metrics['stalled_packages']}. An overall finish is unavailable while any incomplete package has zero recent production. Scenario effectiveness has not been observed. Discrete station/signaling quantities make four-week rates volatile. A zero rate returns no finite finish date."
    decision = "Prioritize S3 possession access and electrification supply review. Its simulated lower productivity and higher cost factor explain weak delivery; this is a designed scenario, not a causal finding from ORR. Confirm access, design and supplier readiness before committing recovery spend. Monitor physical units, weekly earned value, unpaid commitments, overdue actions and forecast movement."
    source = "OBSERVED CONTEXT: ORR table 3181a supplies 96 railway periods of regional delay rates; table 6320 supplies 79 annual nation records. Context is not used to calibrate simulated project progress. ORR data is licensed OGL v3.0; source Network Rail (infrastructure also TfL and Amey Infrastructure Wales). Source URLs and SHA256 hashes: data/manifest.json."
    method = "Baseline assumptions: four sections totaling 68 route-miles, two stations and four signaling installations per section; track GBP1.6m/mile, electrification GBP1.1m/mile, station GBP12m and signal installation GBP2m. Linear time-phased package baselines, 52-week programme, status week30, seed2026. All labour/possession constraints are simplified. Actual physical stations and signal installations are integer-earned; planned fractions can be fractional budget phasing."
    formula = "PV=sum(BAC*planned fraction); EV=sum(BAC*earned physical fraction); AC=sum(cost); CPI=EV/AC; SPI=EV/PV; SV=EV-PV and CV=EV-AC are currency. EAC=AC+(BAC-EV)/CPI, with AC+unpaid commitments as floor. Remaining commitments cover unspent obligations and are not added to EAC again. No contingency is embedded; risk exposure is reported separately and must not be added mechanically because risks may overlap."
    limitations = "Calendar forecasts extrapolate each package's last four intervals independently; this is not a resource-leveled critical-path schedule, and no statistical confidence interval is claimed. Budget-weighted physical progress is not average miles. SPI becomes uninformative at final completion. ORR four-week periods are not months; moving annual values and missing flags are preserved. Route-km and track-km are distinct; infrastructure breaks preclude naive change claims."
    risktext = f"SIMULATED register: six risks; expected monetary exposure GBP {metrics['risk_exposure_gbp']/1e6:.2f}m. Exposure=probability*impact; ordinal score=ceil(probability*5)*impact band, with red>=15, amber>=8. Probability/impact are scenario assumptions. Named accountable roles, mitigations and due dates are in risks.csv."
    source_references = [
        "Office of Rail and Road, Table 3181a (accessed 28 September 2026): "
        + urls["orr_3181a.html"],
        "Office of Rail and Road, Table 6320, infrastructure as of March 2025: "
        + urls["orr_6320.ods"],
        "Licence and reuse terms: https://www.orr.gov.uk/terms-and-conditions",
    ]
    risk_details = [
        f"{row.risk_id} | {row.section} | {row.description}. Probability {row.probability:.0%}; impact GBP {row.impact_gbp/1e6:.2f}m; expected exposure GBP {row.exposure_gbp/1e6:.2f}m; {row.RAG}, ordinal score {row.score}. Owner: {row.owner}. Due: {row.due_date}. Mitigation: {row.mitigation}. Status: open, no closure evidence assumed."
        for row in risks.itertuples()
    ]
    for name, title, secs, figs in [
        (
            "executive_summary",
            "Rail control tower | executive decision",
            [
                ("Business problem", overview),
                ("Action required", decision),
                ("Schedule and recovery", schedule),
                ("Evidence boundary", source),
            ],
            ["01_executive.png", "02_sections.png"],
        ),
        (
            "project_controls_report",
            "Rail project controls | technical evidence",
            [
                ("Status", overview),
                ("Baseline and ledger design", method),
                ("Calculation definitions", formula),
                ("Forecast methods", schedule),
                ("Limitations", limitations),
                ("Traceability and sources", source),
                ("Source references", source_references),
            ],
            ["03_schedule.png", "04_cost.png", "06_forecast.png"],
        ),
        (
            "risk_report",
            "Rail risk register | management review",
            [
                ("Risk method", risktext),
                ("Priority mitigation", decision),
                ("Risk-by-risk action register", risk_details),
                (
                    "Approval and monitoring",
                    "Construction manager owns R01, supply chain manager owns R02. Review weekly; escalation requires overdue mitigation or score>=15. Validate recovery feasibility and approve a formal baseline change before substituting any recovery dates.",
                ),
                ("Limitations", limitations),
                ("Source boundary", source),
            ],
            ["05_risk.png"],
        ),
    ]:
        write_report(
            ROOT / f"reports/{name}.pdf",
            title,
            secs,
            [ROOT / "figures" / f for f in figs],
        )
    pages = [
        "Executive Control Tower",
        "Section Performance",
        "Schedule & Milestones",
        "Cost & Earned Value",
        "Risk Register / Heatmap",
        "Forecast & Recovery Scenarios",
    ]
    html = (
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Meridian Rail Control Tower</title><style>body{font:16px system-ui;background:#eef3f7;color:#12344a;margin:0}header,main{max-width:1100px;margin:auto;padding:24px}header{background:#12344a;color:white}nav{display:flex;flex-wrap:wrap;gap:8px}button{padding:12px;background:#007f82;color:white;border:0;border-radius:5px;cursor:pointer}section{display:none}section.active{display:block}img{width:100%;height:auto}article{padding:20px;background:white;border-radius:8px}.badge{background:#ffe7b0;padding:8px;color:#4b3900}</style><header><h1>Meridian Rail Control Tower</h1><p class="badge">FICTIONAL PROJECT · SIMULATED DATA · INTERACTIVE HTML PROTOTYPE</p><p>'
        + overview
        + "</p></header><main><nav>"
    )
    for i, p in enumerate(pages):
        html += f'<button onclick="show({i})">{p}</button>'
    html += "</nav>"
    imgs = sorted((ROOT / "figures").glob("0[1-6]*.png"))
    descriptions = [overview, decision, method, formula, risktext, schedule]
    for i, (p, f, desc) in enumerate(zip(pages, imgs, descriptions)):
        html += (
            f'<section id="p{i}" class="'
            + ("active" if i == 0 else "")
            + f'"><h2>{p}</h2><article><p>{desc}</p><img src="../figures/{f.name}" alt="{p}; derived from simulated records"></article></section>'
        )
    html += (
        "<details><summary>Observed ORR context, separately sourced</summary><p>"
        + source
        + '</p><img src="../figures/07_orr_context.png" alt="Observed ORR regional delay rates"></details><p>Local CSV exports: <a href="../data/processed/status.csv">Status ledger</a> · <a href="../data/processed/risks.csv">Risk register</a> · <a href="../reports/results.json">Results</a></p></main><script>function show(n){document.querySelectorAll("section").forEach((e,i)=>e.classList.toggle("active",i===n))}</script></html>'
    )
    (ROOT / "dashboard/index.html").write_text(html, encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
