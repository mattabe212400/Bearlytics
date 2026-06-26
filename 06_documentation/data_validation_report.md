# Bearlytics — Data Validation Report

_Generated: 2026-06-25 14:53_

> **Read-only audit. No datasets were modified.**

## Summary

| # | Dataset | Rows | Errors | Warnings | Status |
|---|---------|------|--------|----------|--------|
| 1 | `bears_team_stats_2016_2025.csv` | 10 | 0 | 0 | ✅ Pass |
| 2 | `bears_game_logs_2016_2025.csv` | 165 | 0 | 0 | ✅ Pass |
| 3 | `bears_player_stats_2016_2025.csv` | 196 | 0 | 0 | ✅ Pass |
| 4 | `bears_salary_data_2016_2025.csv` | 1,155 | 0 | 0 | ✅ Pass |
| 5 | `nfl_league_stats_2016_2025.csv` | 320 | 0 | 0 | ✅ Pass |

---

## 1. `bears_team_stats_2016_2025.csv`

**Chicago Bears season-level team statistics (2016–2025)**

**Primary Key:** Season

| Check | Status | Detail |
|-------|--------|--------|
| Shape | ℹ️  INFO | 10 rows × 17 columns |
| Duplicate rows | ✅ OK | No exact duplicate rows |
| Duplicate PKs | ✅ OK | No duplicate primary keys (Season) |
| Missing values | ✅ OK | No unexpected missing or blank values |
| Season range | ✅ OK | All in range 2016–2025; seasons: [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025] |
| Numeric: Season | ✅ OK | dtype=int64 |
| Numeric: Wins | ✅ OK | dtype=int64 |
| Numeric: Losses | ✅ OK | dtype=int64 |
| Numeric: Ties | ✅ OK | dtype=int64 |
| Numeric: Points_For | ✅ OK | dtype=int64 |
| Numeric: Points_Against | ✅ OK | dtype=int64 |
| Numeric: Point_Differential | ✅ OK | dtype=int64 |
| Numeric: Games_Played | ✅ OK | dtype=int64 |
| Numeric: Passing_Yards | ✅ OK | dtype=int64 |
| Numeric: Rushing_Yards | ✅ OK | dtype=int64 |
| Numeric: Total_Offense_Yards | ✅ OK | dtype=int64 |
| Numeric: Passing_TDs | ✅ OK | dtype=int64 |
| Numeric: Rushing_TDs | ✅ OK | dtype=int64 |
| Numeric: Total_TDs | ✅ OK | dtype=int64 |
| Numeric: Turnovers | ✅ OK | dtype=int64 |
| Numeric: Takeaways | ✅ OK | dtype=int64 |
| Numeric: Turnover_Differential | ✅ OK | dtype=int64 |

---

## 2. `bears_game_logs_2016_2025.csv`

**Chicago Bears game-by-game results (2016–2025)**

**Primary Key:** Season, Week

| Check | Status | Detail |
|-------|--------|--------|
| Shape | ℹ️  INFO | 165 rows × 12 columns |
| Duplicate rows | ✅ OK | No exact duplicate rows |
| Duplicate PKs | ✅ OK | No duplicate primary keys (Season, Week) |
| Missing values | ✅ OK | No unexpected missing or blank values |
| Season range | ✅ OK | All in range 2016–2025; seasons: [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025] |
| Numeric: Season | ✅ OK | dtype=int64 |
| Numeric: Week | ✅ OK | dtype=int64 |
| Numeric: Points_For | ✅ OK | dtype=int64 |
| Numeric: Points_Against | ✅ OK | dtype=int64 |
| Numeric: Point_Differential | ✅ OK | dtype=int64 |
| Numeric: Wins_After_Game | ✅ OK | dtype=int64 |
| Numeric: Losses_After_Game | ✅ OK | dtype=int64 |
| Numeric: Ties_After_Game | ✅ OK | dtype=int64 |

---

## 3. `bears_player_stats_2016_2025.csv`

**Chicago Bears individual player statistics (2016–2025)**

**Primary Key:** Season, Player_Name

| Check | Status | Detail |
|-------|--------|--------|
| Shape | ℹ️  INFO | 196 rows × 16 columns |
| Duplicate rows | ✅ OK | No exact duplicate rows |
| Duplicate PKs | ✅ OK | No duplicate primary keys (Season, Player_Name) |
| Missing values | ✅ OK | No unexpected missing or blank values |
| Missing: Position | ℹ️  INFO | 17/196 (9%) — intentionally blank (source limitation) |
| Season range | ✅ OK | All in range 2016–2025; seasons: [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025] |
| Numeric: Season | ✅ OK | dtype=int64 |
| Numeric: Games_Played | ✅ OK | dtype=int64 |
| Numeric: Passing_Yards | ✅ OK | dtype=int64 |
| Numeric: Passing_TDs | ✅ OK | dtype=int64 |
| Numeric: Interceptions_Thrown | ✅ OK | dtype=int64 |
| Numeric: Rushing_Yards | ✅ OK | dtype=int64 |
| Numeric: Rushing_TDs | ✅ OK | dtype=int64 |
| Numeric: Receiving_Yards | ✅ OK | dtype=int64 |
| Numeric: Receiving_TDs | ✅ OK | dtype=int64 |
| Numeric: Receptions | ✅ OK | dtype=int64 |
| Numeric: Targets | ✅ OK | dtype=int64 |
| Numeric: Total_Yards | ✅ OK | dtype=int64 |
| Numeric: Total_TDs | ✅ OK | dtype=int64 |
| Team abbreviation | ✅ OK | All Team values are 'CHI' |
| Player names | ✅ OK | No whitespace issues in Player_Name |

---

## 4. `bears_salary_data_2016_2025.csv`

**Chicago Bears player contract data (signed through ~April 2022)**

**Primary Key:** Season, Player_Name

| Check | Status | Detail |
|-------|--------|--------|
| Shape | ℹ️  INFO | 1,155 rows × 7 columns |
| Duplicate rows | ✅ OK | No exact duplicate rows |
| Duplicate PKs | ✅ OK | No duplicate primary keys (Season, Player_Name) |
| Missing values | ✅ OK | No unexpected missing or blank values |
| Season range | ✅ OK | All in range 2016–2025; seasons: [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025] |
| Numeric: Season | ✅ OK | dtype=int64 |
| Numeric: Contract_Value | ✅ OK | dtype=int64 |
| Numeric: Guaranteed_Money | ✅ OK | dtype=int64 |
| Numeric: Contract_Length_Years | ✅ OK | dtype=int64 |
| Team abbreviation | ✅ OK | All Team values are 'CHI' |
| Player names | ✅ OK | No whitespace issues in Player_Name |

---

## 5. `nfl_league_stats_2016_2025.csv`

**League-wide season statistics for all NFL teams (2016–2025)**

**Primary Key:** Season, Team

| Check | Status | Detail |
|-------|--------|--------|
| Shape | ℹ️  INFO | 320 rows × 19 columns |
| Duplicate rows | ✅ OK | No exact duplicate rows |
| Duplicate PKs | ✅ OK | No duplicate primary keys (Season, Team) |
| Missing values | ✅ OK | No unexpected missing or blank values |
| Season range | ✅ OK | All in range 2016–2025; seasons: [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025] |
| Numeric: Season | ✅ OK | dtype=int64 |
| Numeric: Wins | ✅ OK | dtype=int64 |
| Numeric: Losses | ✅ OK | dtype=int64 |
| Numeric: Ties | ✅ OK | dtype=int64 |
| Numeric: Win_Percentage | ✅ OK | dtype=float64 |
| Numeric: Points_For | ✅ OK | dtype=int64 |
| Numeric: Points_Against | ✅ OK | dtype=int64 |
| Numeric: Point_Differential | ✅ OK | dtype=int64 |
| Numeric: Passing_Yards | ✅ OK | dtype=int64 |
| Numeric: Rushing_Yards | ✅ OK | dtype=int64 |
| Numeric: Total_Offense_Yards | ✅ OK | dtype=int64 |
| Numeric: Passing_TDs | ✅ OK | dtype=int64 |
| Numeric: Rushing_TDs | ✅ OK | dtype=int64 |
| Numeric: Turnovers | ✅ OK | dtype=int64 |
| Numeric: Takeaways | ✅ OK | dtype=int64 |
| Numeric: Turnover_Differential | ✅ OK | dtype=int64 |
| Numeric: Offensive_Rank | ✅ OK | dtype=int64 |
| Numeric: Defensive_Rank | ✅ OK | dtype=int64 |
| CHI in dataset | ✅ OK | CHI appears in 10 rows |

---

_End of report_