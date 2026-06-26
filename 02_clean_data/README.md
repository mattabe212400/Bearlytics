# Phase 2: Clean Data

**Project:** Bearlytics — Chicago Bears BI Dashboard  
**Author:** Matt Abraham  
**Phase:** 2 of 4 — ETL, Cleaning & Validation  

---

## Overview

Phase 2 takes the ten per-season raw CSV files from Phase 1 and consolidates them into master datasets ready for a database. This phase also builds the dimension tables that give the star schema its structure, and runs a full data quality audit to confirm every file is clean before anything gets imported into SQLite.

By the end of Phase 2 there are 9 files — 5 fact tables and 4 dimension tables — all validated with zero errors and zero warnings.

---

## What's in This Folder

| Folder | Contents |
|--------|---------|
| `fact_tables/` | 5 consolidated master CSVs — one per subject area, all seasons combined |
| `dimension_tables/` | 4 lookup tables — teams, players, positions, dates |

---

## Fact Tables

| File | Rows | Description |
|------|------|-------------|
| `bears_team_stats_2016_2025.csv` | 10 | Season-level Bears team stats — wins, yards, TDs, turnovers, rankings |
| `bears_game_logs_2016_2025.csv` | 165 | Every regular-season game result with running record |
| `bears_player_stats_2016_2025.csv` | 196 | Offensive skill player stats by season |
| `bears_salary_data_2016_2025.csv` | 1,155 | Player contracts — guaranteed money, total value, contract length |
| `nfl_league_stats_2016_2025.csv` | 320 | All 32 NFL teams by season — used for league-wide comparisons |

---

## Dimension Tables

| File | Rows | Description |
|------|------|-------------|
| `dim_teams.csv` | 32 | All 32 NFL teams with conference, division, city, and nickname |
| `dim_players.csv` | 510 | Bears players across all seasons with position and year range |
| `dim_positions.csv` | 18 | Position codes with position group (Offense / Defense / Special Teams) |
| `date_dimension.csv` | 3,653 | Full calendar 2016–2025 with year, quarter, month, week, day, weekend flag |

---

## Key Columns by Dataset

**`bears_salary_data_2016_2025.csv`**

| Column | Description |
|--------|-------------|
| Season, Player_Name, Position, Team | Player info |
| Guaranteed_Money | Guaranteed dollars in the contract |
| Contract_Value | Total contract value |
| Contract_Length_Years | Contract length in years |

**`dim_players.csv`**

| Column | Description |
|--------|-------------|
| Player_ID | Surrogate key |
| Player_Name | nflverse abbreviated name (e.g., `J.Howard`) |
| Position | Position code |
| First_Season, Last_Season | Year range the player appears in data |

---

## ETL Scripts

The ETL scripts live in `08_scripts/etl/` and read from the `_cache/` files written in Phase 1.

| Script | Output |
|--------|--------|
| `build_bears_team_stats.py` | `fact_tables/bears_team_stats_2016_2025.csv` |
| `build_bears_game_logs.py` | `fact_tables/bears_game_logs_2016_2025.csv` |
| `build_bears_player_stats.py` | `fact_tables/bears_player_stats_2016_2025.csv` |
| `build_bears_salary_data.py` | `fact_tables/bears_salary_data_2016_2025.csv` |
| `build_nfl_league_stats.py` | `fact_tables/nfl_league_stats_2016_2025.csv` |

To rebuild all clean data from the cached source files:

```bash
python 08_scripts/etl/build_bears_team_stats.py
python 08_scripts/etl/build_bears_game_logs.py
python 08_scripts/etl/build_bears_player_stats.py
python 08_scripts/etl/build_bears_salary_data.py
python 08_scripts/etl/build_nfl_league_stats.py
```

---

## Validation

After ETL, all 9 datasets were audited with `08_scripts/validation/validate_datasets.py`. The script checks row counts, duplicate rows, duplicate primary keys, missing values, season range, numeric types, team abbreviation standardization, and player name whitespace — reporting only, no modifications.

**Fact Table Results**

| Dataset | Rows | Errors | Warnings | Status |
|---------|------|--------|----------|--------|
| `bears_team_stats_2016_2025.csv` | 10 | 0 | 0 | ✅ Pass |
| `bears_game_logs_2016_2025.csv` | 165 | 0 | 0 | ✅ Pass |
| `bears_player_stats_2016_2025.csv` | 196 | 0 | 0 | ✅ Pass |
| `bears_salary_data_2016_2025.csv` | 1,155 | 0 | 0 | ✅ Pass |
| `nfl_league_stats_2016_2025.csv` | 320 | 0 | 0 | ✅ Pass |

**Dimension Table Results**

| Dataset | Rows | Errors | Warnings | Status |
|---------|------|--------|----------|--------|
| `date_dimension.csv` | 3,653 | 0 | 0 | ✅ Pass |
| `dim_players.csv` | 510 | 0 | 0 | ✅ Pass |
| `dim_positions.csv` | 18 | 0 | 0 | ✅ Pass |
| `dim_teams.csv` | 32 | 0 | 0 | ✅ Pass |

Full reports are saved to `06_documentation/`:
- `data_validation_report.md` — fact table audit
- `dimension_validation_report.md` — dimension table audit

---

## Clean Data Folder

![Clean Data Folder](../05_screenshots/phase%202/clean_data_folder_vscode_pic.png)

---

## Validation Reports in VS Code

![Data Validation Report](../05_screenshots/phase%202/data_valuation_report_vscode_pic.png)

![Dimension Validation Report](../05_screenshots/phase%202/dimension_valuation_report_vscode_pic.png)

---

## What's Next

Phase 3 takes these 9 clean files, imports them into a SQLite database following a star schema, and runs exploratory and business SQL queries to start drawing conclusions from the data.
