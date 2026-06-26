# Bearlytics — Chicago Bears Analytics Platform

A full-stack business intelligence project analyzing Chicago Bears franchise performance across ten NFL seasons (2016–2025). Built end-to-end — from raw data collection through SQL modeling to an interactive Power BI dashboard — replicating the analytics workflow used by professional BI teams.

![Executive Dashboard](05_screenshots/phase%204/executive_dashboard_page_1.png)

**[View Live Dashboard →](https://app.powerbi.com/view?r=eyJrIjoiZDhjMzEwMTYtZjFmMC00NTE0LWIxNDgtZjdiNmUxMDU0YzMwIiwidCI6IjAzNDdkODlhLTAxNzQtNGRkMy1hZGViLTMzMzljODljMzVmNSIsImMiOjN9)**

---

## Key Findings

- The Bears went **68-97 (41.2% win rate)** over the decade, consistently below the league average of ~8.5 wins per season
- **2018 was the franchise's best season** — 12 wins, a +138 point differential, and their only top-10 offensive and defensive ranking in the study period
- **Turnover differential is the strongest predictor of success** — the best season posted a +22 differential, while negative margins consistently corresponded with losing records
- **2025 showed the clearest offensive improvement** — 441 points scored and ~6,000 total offensive yards, the highest in the decade
- **$1.18bn in total roster investment** was tracked, with edge defenders (ED) and quarterbacks (QB) receiving the largest allocations at $1.7bn and $1.2bn respectively
- **Khalil Mack ($141M) and Jay Cutler ($127M)** held the two largest contracts of the study period

---

## Tech Stack

| Layer | Tools |
|---|---|
| Data Collection | Python, requests, pandas, nflverse |
| Data Validation | Python, pandas |
| Database | SQLite, SQL |
| Business Intelligence | Microsoft Power BI, DAX |

---

## Project Phases

### Phase 1 — Data Collection & Engineering
> *`01_raw_data/` · `08_scripts/data_collection/`*

Pulled data directly from the [nflverse](https://github.com/nflverse/nflverse-data) open-source dataset using Python (requests + pandas). Play-by-play files for each season were downloaded and cached locally to avoid redundant network calls. Five datasets were engineered from raw sources — team stats, game logs, player stats, salary data, and league-wide stats — with per-season CSV files written as output.

**Data collected:** 10 seasons · 5 datasets · play-by-play sourced from nflverse GitHub releases

---

### Phase 2 — Data Validation & Modeling
> *`02_clean_data/` · `08_scripts/validation/` · `06_documentation/`*

All five datasets were validated with automated Python scripts checking for duplicate rows, duplicate primary keys, missing values, season range integrity, and correct data types. Every dataset passed with zero errors across 1,846 total rows.

| Dataset | Rows | Result |
|---|---|---|
| `bears_team_stats_2016_2025.csv` | 10 | ✅ Pass |
| `bears_game_logs_2016_2025.csv` | 165 | ✅ Pass |
| `bears_player_stats_2016_2025.csv` | 196 | ✅ Pass |
| `bears_salary_data_2016_2025.csv` | 1,155 | ✅ Pass |
| `nfl_league_stats_2016_2025.csv` | 320 | ✅ Pass |

---

### Phase 3 — SQL Database & Business Analysis
> *`03_sql/`*

A relational SQLite database was built using a star schema with 9 tables (4 dimension + 5 fact). Business queries answered executive-level questions across five categories: season performance trends, playoff contention history, Bears vs. league average benchmarking, player production analysis, and roster salary efficiency.

**Schema:** `dim_teams` · `dim_players` · `dim_positions` · `date_dimension` · `fact_team_stats` · `fact_game_logs` · `fact_player_stats` · `fact_salary_data` · `fact_nfl_league_stats`

---

### Phase 4 — Power BI Development & DAX Modeling
> *`04_powerbi/`*

The validated SQL model was imported into Power BI and rebuilt as a semantic data model with one-to-many star schema relationships. 30+ reusable DAX measures were created for dynamic business calculations. Five interactive dashboard pages were developed, each answering a distinct business question.

| Page | Business Question |
|---|---|
| Executive Summary | How has the franchise performed over the last decade? |
| Team Performance | Which areas of team performance improved or declined? |
| Player Performance | Which players drove offensive success? |
| Roster Investment | How effectively was roster spending converted into wins? |
| Franchise Insights | What are the key long-term takeaways? |

![Franchise Insights](05_screenshots/phase%204/franchise_insights_page_5.png)

---

## Dashboard Screenshots

| | |
|---|---|
| ![Executive Summary](05_screenshots/phase%204/executive_dashboard_page_1.png) | ![Team Performance](05_screenshots/phase%204/team_performance_page_2.png) |
| **Executive Summary** | **Team Performance** |
| ![Player Performance](05_screenshots/phase%204/player_performance_page_3.png) | ![Roster Investment](05_screenshots/phase%204/roster_investment_page_4.png) |
| **Player Performance** | **Roster Investment** |

---

## Repository Structure

```
Bearlytics Project/
├── 01_raw_data/          Raw nflverse data and play-by-play cache
├── 02_clean_data/        Validated, consolidated fact table CSVs
├── 03_sql/               SQLite schema, validation, and business queries
├── 04_powerbi/           Power BI report (.pbix) and phase README
├── 05_screenshots/       Dashboard screenshots by phase
├── 06_documentation/     Phase documentation PDFs
├── 07_readme/            This file
└── 08_scripts/           Python ETL and validation scripts
```

---

## Project Stats

| Metric | Value |
|---|---|
| Seasons covered | 2016–2025 (10 seasons) |
| Total data rows | 1,846 |
| SQL tables | 9 |
| DAX measures | 30+ |
| Power BI dashboard pages | 5 |
| Dashboard visualizations | 30+ |

---

*Data source: [nflverse](https://github.com/nflverse/nflverse-data) · MIS Portfolio Project*
