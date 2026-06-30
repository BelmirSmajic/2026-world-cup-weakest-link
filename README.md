# 2026 World Cup Weakest-Link Analysis

**Created by Belmir Smajic**

**Thesis:** A national team's lowest-valued Core XI starters may reveal lineup fragility that total lineup value and star-player value can conceal.

[View the GitHub Pages case study](https://BelmirSmajic.github.io/2026-world-cup-weakest-link/)

## Executive Summary

This project reconstructs a Core XI for all 48 teams in the 2026 World Cup field, assigns a player-value field to all 528 selected players, and tests whether the bottom three Core XI players by value are associated with group-stage performance.

The final dataset is complete: **528 of 528 players valued**, **48 of 48 teams complete**, **0 missing values**, **0 duplicate team-player rows**, and **0 USD conversion errors**.

The primary metric is **bottom-three Core XI average value in USD**, a lineup-floor measure intended to capture how exposed a team may be once play moves past its stars.

## Business Question

Does a team's lineup floor track World Cup performance better than total lineup value or star-player value?

In portfolio terms, this is a sports analytics version of a depth-risk question: is the weakest part of a system more informative than its headline strength?

## Key Findings

Weakest bottom-three lineup floors:

- 1. IR Iran: $0.12M bottom-three average, 3 points
- 2. Curacao: $0.14M bottom-three average, 1 point
- 3. Cabo Verde: $0.20M bottom-three average, 3 points
- 4. New Zealand: $0.20M bottom-three average, 1 point
- 5. Qatar: $0.23M bottom-three average, 1 point

Strongest bottom-three lineup floors:

- 1. England: $45.17M bottom-three average, 7 points
- 2. France: $26.69M bottom-three average, 9 points
- 3. Germany: $21.18M bottom-three average, 6 points
- 4. Spain: $19.39M bottom-three average, 7 points
- 5. Netherlands: $18.63M bottom-three average, 7 points

Spearman relationships in the observed group-stage sample:

- Bottom-three average vs points: `0.771`
- Total Core XI value vs points: `0.719`
- Top-three average vs points: `0.699`
- Bottom-three average vs goal difference: `0.751`

Advancement by bottom-three value quartile:

| Quartile | Teams | Advancement Rate | Avg Points | Avg GD | Avg Bottom-Three Value |
| --- | ---: | ---: | ---: | ---: | ---: |
| Weakest quartile | 12 | 16.7% | 1.25 | -5.17 | $0.30M |
| Q2 | 12 | 75.0% | 3.83 | -0.67 | $1.01M |
| Q3 | 12 | 83.3% | 4.67 | 1.58 | $2.53M |
| Strongest quartile | 12 | 91.7% | 6.58 | 4.25 | $16.14M |

The results should be read as association, not causation. Player value is a proxy for talent, demand, and market context; it is not a deterministic match model.

## Methodology

1. Reconstructed a Core XI for each team using minutes, starts, appearances, and deterministic tie-breaking.
2. Joined each Core XI player to a valuation source.
3. Converted EUR values to USD using `1 EUR = 1.1406 USD`.
4. Ranked each team's Core XI by player value.
5. Calculated lineup-floor metrics: bottom-one value, bottom-three average, bottom-three total, lineup imbalance, and value shares.
6. Compared these metrics with group-stage points, goal difference, group position, and advancement.

## Dataset And Validation

Published CSV files:

- `data/player_level_analysis.csv`: player-level analysis dataset.
- `data/team_rankings.csv`: final ranking tables.
- `data/source_mix_sensitivity_summary.csv`: source-mix sensitivity result.
- `data/final_value_validation_report.csv`: validation checks.

Validation highlights:

- Valued players: `528 / 528`
- Complete teams: `48 / 48`
- Missing values: `0`
- Duplicate team-player rows: `0`
- USD conversion errors: `0`

## Source Hierarchy And Limitations

FootballTransfers was the primary valuation source. FotMob/SciSports was used as a fallback, and Transfermarkt plus manually verified indexed records filled the final gaps. Source and fallback flags are retained in the dataset.

Final source counts:

- FootballTransfers: 459 players
- FotMob / SciSports: 46 players
- Transfermarkt: 23 players

Fallback-source counts:

- FootballTransfers: 13 fallback players
- FotMob / SciSports: 46 fallback players
- Transfermarkt: 23 fallback players

Source-mix sensitivity: excluding Transfermarkt/manual fallback rows removed `32` player values across `15` teams and left `33` complete teams. The weakest-link top-ten overlap was `8/10`, so the broad weakest-link conclusion was stable, while exact low-end ordering remains less reliable than tiers.

Limitations:

- Mixed valuation models across sources.
- Some fallback values have unverified valuation dates.
- Core XI is reconstructed from available tournament usage data.
- Player value is a market proxy, not a causal performance variable.
- Exact low-end rankings should be interpreted as broad tiers.

## GitHub Pages

The case-study site is designed for GitHub Pages from the `/docs` folder:

https://BelmirSmajic.github.io/2026-world-cup-weakest-link/

## Repository Structure

```text
.
|-- README.md
|-- LICENSE
|-- docs/
|-- data/
|   |-- raw/
|   |-- reference/
|   |-- player_level_analysis.csv
|   |-- team_rankings.csv
|   |-- source_mix_sensitivity_summary.csv
|   `-- final_value_validation_report.csv
|-- analysis/
|-- src/
|-- run_analysis.py
`-- requirements.txt
```

## Reproduction

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_analysis.py
```

The script rebuilds processed data and final CSV outputs from `data/raw/` and `data/reference/`.

## Author

Built by **Belmir Smajic** as a data analytics portfolio project.

## License And Data Notice

Original code is licensed under the MIT License. Third-party football data and player valuations remain subject to their original providers' terms and are included for analytical and portfolio demonstration purposes.
