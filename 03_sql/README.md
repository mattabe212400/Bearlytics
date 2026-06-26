# Phase 3: SQL Analysis

**Project:** Bearlytics — Chicago Bears BI Dashboard  
**Author:** Matt Abraham  
**Phase:** 3 of 4 — SQL Database & Analysis  

---

## Overview

Phase 3 is where the project shifted from raw data and cleaned CSVs into something I could actually query and draw conclusions from. I built a local SQLite database from scratch, wrote a full schema, imported all nine clean datasets, validated the data, and then wrote exploratory and business-focused SQL queries to start pulling real insights out of the Bears' 2016–2025 seasons.

This was my first time designing a database schema from the ground up and writing production-style SQL against real NFL data — not a textbook exercise, not sample data. Actual Bears numbers.

---

## What's in This Folder

| File | Purpose |
|------|---------|
| `01_schema.sql` | DDL — defines all 9 tables with primary keys and data types |
| `02_import.py` | Python script that creates `bearlytics.db` and imports all CSVs |
| `03_validate.sql` | Validation queries — row counts, null checks, duplicate detection, business logic checks |
| `04_exploratory.sql` | 13 EDA queries — first pass at understanding the data |
| `05_business.sql` | 15 business-focused queries (BQ-01 through BQ-15) |
| `06_views.sql` | 7 reusable SQL views used as data sources for Power BI |
| `bearlytics.db` | The live SQLite database |

---

## Database Schema

The database follows a star schema pattern with dimension and fact tables.

**Dimension Tables**
- `dim_teams` — all 32 NFL teams with conference and division
- `dim_players` — Bears player roster across all seasons
- `dim_positions` — position groups (Offense, Defense, Special Teams)
- `date_dimension` — full calendar from 2016–2025

**Fact Tables**
- `fact_team_stats` — Bears season-level totals (wins, yards, TDs, turnovers)
- `fact_game_logs` — individual game results with running record
- `fact_player_stats` — offensive skill player stats by season
- `fact_salary_data` — player contracts and guaranteed money
- `fact_nfl_league_stats` — all 32 teams by season for league comparisons

**Row Counts After Import**

| Table | Rows |
|-------|------|
| dim_teams | 32 |
| dim_players | 510 |
| dim_positions | 18 |
| date_dimension | 3,653 |
| fact_team_stats | 10 |
| fact_game_logs | 165 |
| fact_player_stats | 196 |
| fact_salary_data | 1,155 |
| fact_nfl_league_stats | 320 |

---

## Reusable Views

One of the bigger decisions in this phase was creating views that pre-join and pre-calculate everything so Power BI (Phase 4) can connect directly without needing complex queries on the dashboard side.

| View | What It Does |
|------|-------------|
| `vw_season_summary` | Full season stats + win %, points/yards per game, offensive/defensive rank, season tier label |
| `vw_game_log_detail` | Game results with opponent full name and division |
| `vw_player_season_stats` | Player stats with per-game rates, catch %, and position group |
| `vw_player_career_stats` | Career totals rolled up for every Bears player |
| `vw_salary_efficiency` | Salary data joined to production stats with a Value_Rating label |
| `vw_bears_vs_league` | Bears stats vs NFL averages side by side each season |
| `vw_home_away_by_season` | Home and away win % splits per season |

---

## Sample Queries

### Season Summary — 2016 to 2025

All 10 Bears seasons with win percentage, points per game, yards per game, and a tier label (Playoff Contender / Middle of Pack / Rebuilding).

```sql
SELECT *
FROM vw_season_summary
ORDER BY Season;
```

![Season Summary](../05_screenshots/season_summary_db_pic.png)

---

### Bears vs. NFL Average

Compares Bears points scored, total yards, and offensive/defensive rankings against the league average each season. Shows how far above or below average the Bears were year by year.

```sql
SELECT Season, Wins, CHI_Pts_For, NFL_Avg_Pts_For, Pts_For_vs_Avg,
       CHI_Total_Yards, NFL_Avg_Yards, Yards_vs_Avg,
       Offensive_Rank, Defensive_Rank
FROM vw_bears_vs_league
ORDER BY Season;
```

![Bears vs NFL Average](../05_screenshots/bears_vs_nfl_avg_db_pic.png)

---

### Salary Efficiency

Joins guaranteed contract money against player production (yards and TDs) to flag players as High Value, Fair Value, or Overpaid. This required a name normalization step since the salary dataset used full names and the stats dataset used nflverse abbreviated names.

```sql
SELECT Season, Player_Name, Position, Guaranteed_M, Total_Yards, Total_TDs, Value_Rating
FROM vw_salary_efficiency
WHERE Total_Yards > 0
ORDER BY Guaranteed_M DESC;
```

![Salary Efficiency](../05_screenshots/salary_efficiency_db_pic.png)

---

## A Note on the Name Normalization Challenge

One issue I ran into: the salary data used full player names (`Jordan Howard`, `Mitchell Trubisky`) while the player stats dataset used nflverse abbreviated names (`J.Howard`, `M.Trubisky`). This meant no joins between the two tables worked at all.

I wrote a separate ETL script (`08_scripts/etl/normalize_salary_player_names.py`) to fix this using a 3-pass matching algorithm:

- **Pass 1** — exact match
- **Pass 2** — convert full name to `F.Lastname` format
- **Pass 3** — fuzzy prefix match for edge cases like `Jordan Howard → Jo.Howard` (2017, when nflverse used two characters to distinguish Jordan from Jaye Howard on the same roster)

The script also detects ambiguous cases (like two players with the same initial and last name) and intentionally leaves those unchanged rather than guessing. After normalization, 143 of 1,155 salary rows join to player stats — which is the expected rate since the salary data covers all 90-man roster positions and the stats only track offensive skill players.

---

## How to Rebuild the Database

If you need to rebuild from scratch:

```bash
python 03_sql/02_import.py
```

Then re-apply views and normalize salary names:

```bash
python 08_scripts/etl/normalize_salary_player_names.py
```

---

## What's Next

Phase 4 connects `bearlytics.db` to Power BI and builds the interactive dashboard using the seven views created here as data sources.
