# Tableau Dashboard Build Guide

Workbook title: **2026 World Cup Weakest-Link Analysis**

Dashboard title: **A Team Is Only as Strong as the Bottom of Its Lineup**

Subtitle: **The weakest regular starters had a stronger relationship with World Cup group-stage performance than the biggest stars.**

## Data Sources

Use the packaged CSV files in `tableau_dashboard_uploads/`:

- `team_dashboard.csv`: one row per team with ranks, values, points, advancement status, notable labels, and quartiles.
- `quartile_dashboard.csv`: lineup-floor quartile advancement rates and counts.
- `metric_dashboard.csv`: Spearman comparison values: 0.771, 0.719, 0.699.
- `core_xi_dashboard.csv`: player-level Core XI detail with bottom-three flags.

## Dashboard Layout

Size: 1200 x 900 fixed or automatic with 1200 x 900 design target.

Theme:

- Background: #0d1117
- Card/panel: #151b23 or #1d2632
- Text: #eef4ff
- Muted text: #9fb0c5
- Advanced: #7ee787
- Eliminated: #47c2ff
- Trend/accent: #f2cc60

## Required Copy

Methodology note:

> For each country, a retrospective Core XI was reconstructed from actual group-stage minutes, starts, and appearances. Lineup floor is the average USD value of the three least-valued players within those 11 only, not the cheapest players in the full squad.

Source note:

> Player values were assembled primarily from FootballTransfers, with FotMob/SciSports and Transfermarkt used for controlled fallback coverage. Exact low-end ordering should be interpreted with more caution than broad value tiers.

Add methodology link:

https://belmirsmajic.github.io/2026-world-cup-weakest-link/methodology.html

## Sheets To Create

1. KPI Cards
   - 0.77: relationship between lineup floor and group-stage points.
   - Text: "Teams with stronger lineup floors generally earned more points."
   - Note: "Spearman correlation across 48 teams. Strong relationship, not a guarantee."
   - 92% strongest-quartile advancement.
   - 17% weakest-quartile advancement.
   - 528 players across 48 teams.

2. Main Scatterplot
   - Data source: `team_dashboard.csv`
   - Columns: `bottom_3_average_value_usd`
   - Rows: `points`
   - Color: `advanced_status`
   - Label: `notable_label`
   - Tooltip fields: team, bottom_3_value_label, core_xi_total_value_label, points, goal_difference, advanced_status, lineup_floor_rank_label, total_value_rank_label.
   - Use log x-axis if available.
   - Add trend line.
   - Title: "Teams with stronger lineup floors generally earned more points".

3. Advancement By Quartile
   - Data source: `quartile_dashboard.csv`
   - Sort by `quartile_order`.
   - Show `advancement_rate` as percentage and `advanced_count_label`.
   - Title: "Teams with the strongest lineup floors advanced far more often".

4. Metric Comparison
   - Data source: `metric_dashboard.csv`
   - Bars: `spearman_vs_points`
   - Dimension: `metric`
   - Sort by `rank`.
   - Title: "The weakest three carried slightly more performance signal than the biggest three".
   - Caption: "Higher values indicate a stronger tendency for more valuable teams to earn more points."

5. Rank Comparison
   - Data source: `team_dashboard.csv`
   - Show team, total_value_rank_label, lineup_floor_rank_label, points, advanced_status.
   - Highlight Mexico and Uruguay.
   - Title: "Where lineup floor saw something total value missed".
   - Annotation: "Mexico's total value made it look weaker than the depth of its regular lineup suggested. Uruguay showed the opposite pattern."

6. Team Detail
   - Data source: `core_xi_dashboard.csv`
   - Filter: team selector, single value.
   - Columns: player, position, minutes, starts, appearances, market_value_usd_label, value_source.
   - Highlight `lineup_floor_player`.
   - The three `Lineup-floor player` rows should be visually distinct.

7. Strongest and Weakest Tables
   - Data source: `team_dashboard.csv`
   - Strongest: lineup_floor_rank 1 through 5.
   - Weakest: lineup_floor_rank 44 through 48, sorted ascending by `bottom_3_average_value_usd` or reverse rank display.
   - Explicit values: use `bottom_3_value_label`.
   - Note: all five strongest advanced; four of the five weakest were eliminated; Cabo Verde was the exception.

## Interactions

- Add team filter using `team_dashboard.team`.
- Add dashboard action: selecting a scatterplot mark filters the Core XI detail.
- Add advanced/eliminated filter if space allows.
- Keep filters visible but compact.

## Verified Values

- Mexico: total-value rank 31st, lineup-floor rank 16th, 9 points, advanced.
- Uruguay: total-value rank 14th, lineup-floor rank 22nd, 2 points, eliminated.
- Strongest quartile: 11 of 12 advanced, 91.7%.
- Weakest quartile: 2 of 12 advanced, 16.7%.
- Spearman values: 0.771, 0.719, 0.699.

## Publish Metadata

Title: **2026 World Cup Weakest-Link Analysis**

Description:

> An interactive analysis of 528 players across all 48 World Cup teams, testing whether the value of the weakest three players in each retrospective usage-based Core XI was more closely related to group-stage results than total lineup value or star power.

Include:

https://belmirsmajic.github.io/2026-world-cup-weakest-link/

Tags: World Cup, football, soccer, sports analytics, Tableau, data visualization, market value
