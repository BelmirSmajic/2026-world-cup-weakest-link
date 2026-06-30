# Final USD Weakest-Link Analysis

## Validation
- valued_players: 528 / expected 528 (pass)
- complete_teams: 48 / expected 48 (pass)
- missing_values: 0 / expected 0 (pass)
- duplicate_player_rows: 0 / expected 0 (pass)
- usd_conversion_bad_rows: 0 / expected 0 (pass)
- source_or_flag_bad_rows: 0 / expected 0 (pass)

## Fallback Source Mix
- FootballTransfers: 13
- FotMob / SciSports: 46
- Transfermarkt: 23

## Weakest Core XI Bottom-Three Values
| rank | team | value_usd_m_display | points | goal_difference | advanced_flag |
| --- | --- | --- | --- | --- | --- |
| 1 | IR Iran | $0.12M | 3 | 0 | False |
| 2 | Curaçao | $0.14M | 1 | -8 | False |
| 3 | Cabo Verde | $0.20M | 3 | 0 | True |
| 4 | New Zealand | $0.20M | 1 | -6 | False |
| 5 | Qatar | $0.23M | 1 | -8 | False |
| 6 | Haiti | $0.26M | 0 | -6 | False |
| 7 | Jordan | $0.30M | 0 | -5 | False |
| 8 | Panama | $0.30M | 0 | -4 | False |
| 9 | Iraq | $0.40M | 0 | -11 | False |
| 10 | Uzbekistan | $0.49M | 0 | -9 | False |

## Strongest Core XI Bottom-Three Values
| rank | team | value_usd_m_display | points | goal_difference | advanced_flag |
| --- | --- | --- | --- | --- | --- |
| 1 | England | $45.17M | 7 | 4 | True |
| 2 | France | $26.69M | 9 | 8 | True |
| 3 | Germany | $21.18M | 6 | 6 | True |
| 4 | Spain | $19.39M | 7 | 5 | True |
| 5 | Netherlands | $18.63M | 7 | 6 | True |
| 6 | Portugal | $14.07M | 5 | 5 | True |
| 7 | Argentina | $10.04M | 9 | 7 | True |
| 8 | Norway | $9.43M | 6 | 1 | True |
| 9 | Türkiye | $9.43M | 3 | -2 | False |
| 10 | Morocco | $9.35M | 7 | 3 | True |

## Balance Extremes
Most balanced lineups by top-three average divided by bottom-three average:
| rank | team | lineup_imbalance_display | points | goal_difference | advanced_flag |
| --- | --- | --- | --- | --- | --- |
| 1 | England | 2.86 | 7 | 4 | True |
| 2 | South Africa | 3.90 | 4 | -1 | True |
| 3 | Netherlands | 5.03 | 7 | 6 | True |
| 4 | Germany | 5.23 | 6 | 6 | True |
| 5 | France | 5.46 | 9 | 8 | True |
| 6 | Japan | 5.91 | 5 | 4 | True |
| 7 | Mexico | 6.11 | 9 | 6 | True |
| 8 | Saudi Arabia | 6.19 | 2 | -4 | False |
| 9 | Iraq | 6.40 | 0 | -11 | False |
| 10 | Morocco | 6.88 | 7 | 3 | True |

Most top-heavy lineups by the same ratio:
| rank | team | lineup_imbalance_display | points | goal_difference | advanced_flag |
| --- | --- | --- | --- | --- | --- |
| 1 | Egypt | 59.17 | 5 | 2 | True |
| 2 | Ecuador | 51.80 | 4 | 0 | True |
| 3 | Uzbekistan | 47.60 | 0 | -9 | False |
| 4 | Colombia | 47.35 | 7 | 3 | True |
| 5 | Uruguay | 41.30 | 2 | -1 | False |
| 6 | Sweden | 40.69 | 4 | 0 | True |
| 7 | Ghana | 35.98 | 4 | 0 | True |
| 8 | Haiti | 35.19 | 0 | -6 | False |
| 9 | Algeria | 33.27 | 4 | -2 | True |
| 10 | Congo DR | 31.05 | 4 | 1 | True |

## Sensitivity
Excluding Transfermarkt/manual fallback rows removes 32 player values across 15 teams, leaving 33 complete teams. The weakest-link top-ten overlap is 8/10, so the weakest-link conclusion is broadly stable under this source-mix check.

## Main Takeaway
The weakest Core XI bottom-three values are concentrated among teams that did not advance or advanced with very low aggregate squad value. Cabo Verde is the notable low-value exception that still advanced, while England, France, Germany, Spain, and the Netherlands have the strongest bottom-three depth.
