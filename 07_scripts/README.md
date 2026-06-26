# Phase 1 & 2 — Python Scripts

All Python scripts used across Bearlytics for data collection, ETL, data modeling, validation, and database import. Scripts are organized by function and designed to run in order — each phase builds on the output of the previous one.

---

## Folder Structure

```
07_scripts/
├── data_collection/     Download raw data from nflverse
├── etl/                 Build and consolidate fact table CSVs
├── data_modeling/       Build dimension table CSVs
├── validation/          Audit clean datasets for quality issues
└── sql/                 Import CSVs into SQLite database
```

---

## data_collection/

Scripts that pull raw data directly from the [nflverse](https://github.com/nflverse/nflverse-data) GitHub releases. Files are cached in `01_raw_data/_cache/` so re-runs skip the download.

| Script | What It Does |
|---|---|
| `download_nflverse_data.py` | Downloads play-by-play files (one per season) and the master schedules file. Computes Bears team stats — wins, losses, points, passing/rushing yards, turnovers, offensive/defensive rankings — from raw PBP data and writes one CSV per season to `01_raw_data/team_stats/` |
| `download_nfl_team_logos.py` | Downloads PNG logos for all 32 NFL teams from nflverse and saves them to `01_raw_data/logos/` |

**Run order:** Run these first before any ETL scripts.

```bash
python 07_scripts/data_collection/download_nflverse_data.py
```

---

## etl/

ETL scripts that transform raw per-season CSVs into consolidated master files ready for validation and database import. Each script reads from `01_raw_data/` and writes a combined CSV to `02_clean_data/fact_tables/`.

| Script | Input | Output |
|---|---|---|
| `build_bears_team_stats.py` | `01_raw_data/team_stats/bears_team_stats_YYYY.csv` | `bears_team_stats_2016_2025.csv` |
| `build_bears_game_logs.py` | `01_raw_data/_cache/schedules.csv` | `bears_game_logs_2016_2025.csv` |
| `build_bears_player_stats.py` | `01_raw_data/player_stats/bears_player_stats_YYYY.csv` | `bears_player_stats_2016_2025.csv` |
| `build_bears_salary_data.py` | `01_raw_data/_cache/contracts/historical_contracts.csv.gz` | `bears_salary_data_2016_2025.csv` |
| `build_nfl_league_stats.py` | `01_raw_data/league_stats/nfl_league_stats_YYYY.csv` | `nfl_league_stats_2016_2025.csv` |

`build_bears_game_logs.py` also computes running season record (wins/losses/ties after each game) and home/away splits directly from the schedules cache.

**Run order:** Run after `data_collection/`.

---

## data_modeling/

Scripts that build the four dimension tables used in the star schema. These don't pull from nflverse — they construct lookup tables from the clean data or static definitions.

| Script | Output |
|---|---|
| `create_dim_teams.py` | All 32 NFL franchises with conference, division, city, and nickname |
| `create_dim_players.py` | All Bears players across 2016–2025 with position, first season, last season |
| `create_dim_positions.py` | 18 positions grouped into Offense, Defense, and Special Teams |
| `create_date_dimension.py` | Full calendar from 2016–2025 (3,653 rows) with year, season, week, day attributes |

**Run order:** Run after `etl/`, before `sql/`.

---

## validation/

Read-only audit scripts that verify data quality without modifying any files. Output goes to both the terminal and a markdown report in `06_documentation/`.

| Script | What It Checks |
|---|---|
| `validate_datasets.py` | Audits all 5 fact table CSVs — duplicate rows, duplicate primary keys, missing values, season range (2016–2025), numeric types, Bears team abbreviation standardization |
| `validate_dimension_tables.py` | Audits the 4 dimension table CSVs — completeness, expected row counts, referential integrity |

All 5 fact datasets and 4 dimension tables passed with zero errors.

**Run order:** Run after `etl/` and `data_modeling/` to confirm clean data before importing to SQL.

```bash
python 07_scripts/validation/validate_datasets.py
```

---

## sql/

| Script | What It Does |
|---|---|
| `02_import.py` | Creates `bearlytics.db` (SQLite), applies the schema from `03_sql/01_schema.sql`, and bulk-imports all 9 clean CSVs into their respective tables |

**Run order:** Run last, after all ETL, modeling, and validation is complete.

```bash
python 07_scripts/sql/02_import.py
```

---

## Full Run Order

```
1. data_collection/download_nflverse_data.py
2. etl/build_bears_team_stats.py
3. etl/build_bears_game_logs.py
4. etl/build_bears_player_stats.py
5. etl/build_bears_salary_data.py
6. etl/build_nfl_league_stats.py
7. data_modeling/create_dim_teams.py
8. data_modeling/create_dim_players.py
9. data_modeling/create_dim_positions.py
10. data_modeling/create_date_dimension.py
11. validation/validate_datasets.py
12. validation/validate_dimension_tables.py
13. sql/02_import.py
```

## Dependencies

```bash
pip install requests pandas
```

No additional packages required — SQLite is included in Python's standard library.
