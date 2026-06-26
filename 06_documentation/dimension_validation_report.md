# Bearlytics — Dimension Table Validation Report

_Generated: 2026-06-25 15:20_

> **Read-only audit. No datasets were modified.**

## Summary

| # | Dimension Table | Rows | Errors | Warnings | Status |
|---|-----------------|------|--------|----------|--------|
| 1 | `date_dimension.csv` | 3,653 | 0 | 0 | ✅ Pass |
| 2 | `dim_players.csv` | 510 | 0 | 0 | ✅ Pass |
| 3 | `dim_positions.csv` | 18 | 0 | 0 | ✅ Pass |
| 4 | `dim_teams.csv` | 32 | 0 | 0 | ✅ Pass |

---

## 1. `date_dimension.csv`

**Primary Key:** `Date`

| Check | Status | Detail |
|-------|--------|--------|
| Shape | ℹ️  INFO | 3,653 rows × 10 columns |
| Duplicate PKs | ✅ OK | No duplicates in 'Date' |
| Missing values | ✅ OK | No missing or blank values |

---

## 2. `dim_players.csv`

**Primary Key:** `Player_ID`

| Check | Status | Detail |
|-------|--------|--------|
| Shape | ℹ️  INFO | 510 rows × 5 columns |
| Duplicate PKs | ✅ OK | No duplicates in 'Player_ID' |
| Missing values | ✅ OK | No missing or blank values |

---

## 3. `dim_positions.csv`

**Primary Key:** `Position_ID`

| Check | Status | Detail |
|-------|--------|--------|
| Shape | ℹ️  INFO | 18 rows × 3 columns |
| Duplicate PKs | ✅ OK | No duplicates in 'Position_ID' |
| Missing values | ✅ OK | No missing or blank values |
| Position_Group values | ✅ OK | All values are valid: ['Defense', 'Offense', 'Special Teams'] |
| Player stats coverage | ✅ OK | All 11 position(s) from player stats are covered by dim_positions |

---

## 4. `dim_teams.csv`

**Primary Key:** `Team_ID`

| Check | Status | Detail |
|-------|--------|--------|
| Shape | ℹ️  INFO | 32 rows × 7 columns |
| Duplicate PKs | ✅ OK | No duplicates in 'Team_ID' |
| Missing values | ✅ OK | No missing or blank values |
| Team count | ✅ OK | Exactly 32 teams present |
| League stats coverage | ✅ OK | All 32 teams from nfl_league_stats are covered by dim_teams |

---

_End of report_