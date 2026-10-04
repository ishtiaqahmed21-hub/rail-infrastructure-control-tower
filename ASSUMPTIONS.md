# Assumptions and analytical boundaries

Fictional Meridian is an independent portfolio scenario inspired by a job simulation. It is not Siemens or Network Rail work and not affiliated with either organisation.

The 68 route-mile project contains S1=18, S2=16, S3=20, S4=14 miles. Each has track, electrification, two stations and four signaling installations. Baseline track weeks 0–40, electrification 8–47, stations 4–44, signaling 15–52. Budget rates: GBP1.6m/track mile, GBP1.1m/electrified route mile, GBP12m/station and GBP2m/signaling installation. Linear package budgets are assumptions. Stations/signaling earn only completed integer units; planned fractions are budget phasing.

The deterministic simulation uses seed 2026. Section production factors [.99,.94,.74,.91], electrification additional .96 factor, weekly uniform noise [.9,1.1], section cost factors [1.02,1.07,1.22,1.10] and 1% phase-related overhead. Outstanding commitments equal 65% of unearned baseline scope cost; they are remaining obligations excluding AC. These assumptions deliberately create an S3 intervention case. All remaining commitments and risk parameters are fictional.

Recovery assumes 25% higher recent production and 8% more remaining forecast cost. It does not prove recovery will work. Forecasts independently extrapolate last four weekly intervals. Any stalled incomplete package makes whole-project finish unavailable; only the latest forecastable package date is reported. These are planning scenarios, not statistical confidence intervals or resource-leveled critical-path schedules. Dependencies, holidays, possessions and resource conflicts require a production scheduler before use.

EAC assumes persistent CPI and is floored at AC+remaining commitments. Risks are separate, may be correlated, and their expected values are not mechanically added to EAC. No contingency reserve or approved changes is assumed. A real implementation requires change control and baseline versioning.
