# Phase 1: Raw Data Collection

**Project:** Bearlytics — Chicago Bears BI Dashboard  
**Author:** Matt Abraham  
**Phase:** 1 of 4 — Data Collection & Source Files  

---

## Overview

Phase 1 is where the project starts — pulling raw NFL data from nflverse, an open-source repository of play-by-play data, schedules, player stats, contracts, and team info. All data covers the 2016–2025 regular seasons, giving a full decade of Bears history to work with.

The collection scripts are in `08_scripts/data_collection/` and `08_scripts/etl/`. Nothing in this folder is manually entered — every file here is either downloaded directly from nflverse GitHub releases or computed from those downloads.

---

## What's in This Folder

| Folder | Contents |
|--------|---------|
| `team_stats/` | 10 season-level CSV files — Bears wins, yards, TDs, turnovers, rankings (one per season) |
| `game_logs/` | 10 season game-by-game CSV files — week, opponent, result, running record |
| `player_stats/` | 10 season player stat CSV files — passing, rushing, receiving, games played |
| `league_stats/` | 10 season all-32-teams CSV files — used for league comparison |
| `logos/` | 32 NFL team logos (PNG) + Bears logo + NFL logo |
| `_cache/` | Cached nflverse source files — schedules, play-by-play (`.csv.gz`), contracts, player stats |

---

## Data Sources

All data comes from the [nflverse](https://github.com/nflverse/nflverse-data) open-source project via GitHub releases.

| Source File | Used For |
|-------------|---------|
| `schedules/games.csv` | Game results, scores, home/away |
| `pbp/play_by_play_{year}.csv.gz` | Yards, TDs, turnovers, third down %, red zone % |
| `contracts/historical_contracts.csv.gz` | Player salary and guaranteed money |
| `player_stats/player_stats.csv` | Individual offensive player stats by season |

Play-by-play files are the heaviest source — one compressed `.csv.gz` per season, cached locally so re-runs skip re-downloading.

---

## File Structure — Raw Dataset Columns

**`team_stats/bears_team_stats_{year}.csv`**

| Column | Description |
|--------|-------------|
| Season | NFL season year |
| Wins, Losses, Ties | Regular season record |
| Points_For, Points_Against, Point_Differential | Scoring |
| Games_Played | Number of regular season games |
| Passing_Yards, Rushing_Yards, Total_Offense_Yards | Offensive yardage |
| Passing_TDs, Rushing_TDs, Total_TDs | Touchdowns |
| Turnovers, Takeaways, Turnover_Differential | Ball security |

**`game_logs/bears_game_log_{year}.csv`**

| Column | Description |
|--------|-------------|
| Season, Week, Game_Date | When the game was played |
| Opponent | Opposing team abbreviation |
| Home_Away | Home or Away |
| Result | W / L / T |
| Points_For, Points_Against, Point_Differential | Game score |
| Wins_After_Game, Losses_After_Game, Ties_After_Game | Running record |

**`player_stats/bears_player_stats_{year}.csv`**

| Column | Description |
|--------|-------------|
| Season, Player_Name, Position, Team | Player info |
| Passing_Yards, Passing_TDs, Interceptions_Thrown | Passing |
| Rushing_Yards, Rushing_TDs | Rushing |
| Targets, Receptions, Receiving_Yards, Receiving_TDs | Receiving |
| Games_Played, Total_Yards, Total_TDs | Summary |

**`league_stats/nfl_league_stats_{year}.csv`**

| Column | Description |
|--------|-------------|
| Season, Team | Season and team abbreviation |
| Wins, Losses, Ties, Win_Percentage | Record |
| Points_For, Points_Against, Point_Differential | Scoring |
| Passing_Yards, Rushing_Yards, Total_Offense_Yards | Offense |
| Passing_TDs, Rushing_TDs, Turnovers, Takeaways, Turnover_Differential | Production |
| Offensive_Rank, Defensive_Rank | League rankings |

---

## How to Re-Run Data Collection

The scripts are in `08_scripts/`. They pull directly from nflverse GitHub releases and write output here.

```bash
# Team stats + game logs (requires nflverse cache)
python 08_scripts/data_collection/download_nflverse_data.py

# Team logos
python 08_scripts/data_collection/download_nfl_team_logos.py

# ETL scripts rebuild the per-season files from cached nflverse data
python 08_scripts/etl/build_bears_team_stats.py
python 08_scripts/etl/build_bears_game_logs.py
python 08_scripts/etl/build_bears_player_stats.py
python 08_scripts/etl/build_bears_salary_data.py
python 08_scripts/etl/build_nfl_league_stats.py
```

PBP cache files are large (~100–300 MB each uncompressed). The scripts skip re-downloading if the `.csv.gz` already exists in `_cache/`.

---

## Raw Data Folder

![Raw Data Folder](../05_screenshots/phase%201/raw_data_folder_vscode_pic.png)

---

## What's Next

Phase 2 takes these per-season raw files and consolidates them into master datasets, builds dimension tables, and validates data quality before anything goes into the database.
