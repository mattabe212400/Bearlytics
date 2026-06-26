#!/usr/bin/env python3
"""
build_team_stats_from_raw.py

Reads pre-downloaded nflverse cache files and builds cleaned
Chicago Bears team season summaries.

Does NOT download anything — run download_team_stats.py first.

Input (must already exist):
  01_raw_data/_cache/schedules.csv
  01_raw_data/_cache/pbp_{year}.csv.gz   (2016 through 2025)

Output:
  01_raw_data/team_stats/bears_team_stats_{year}.csv   — one file per season
  03_clean_data/bears_team_stats_2016_2025.csv          — combined master file

Column sources:
  FROM schedules.csv  : Season, Wins, Losses, Ties, Points_For, Points_Against,
                        Point_Differential, Games_Played
  FROM pbp_{year}.csv : Passing_Yards, Rushing_Yards, Total_Offense_Yards,
                        Passing_TDs, Rushing_TDs, Total_TDs,
                        Turnovers, Takeaways, Turnover_Differential

Notes on Total_TDs:
  Includes offensive passing TDs, offensive rushing TDs, and all defensive /
  special-teams TDs (pick-6s, fumble-return TDs, kick/punt-return TDs).
  Only regular-season games and plays are counted throughout.
"""

import os
import sys

import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TEAM    = "CHI"
SEASONS = list(range(2016, 2026))   # 2016 through 2025 inclusive

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR  = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "01_raw_data", "_cache"))
SEASON_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "01_raw_data", "team_stats"))
CLEAN_DIR  = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "03_clean_data"))

# Only load the PBP columns this script actually uses
LOAD_COLS = [
    "season_type",
    "posteam",
    "defteam",
    "play_type",
    "passing_yards",
    "rushing_yards",
    "pass_touchdown",
    "rush_touchdown",
    "return_touchdown",
    "interception",
    "fumble_lost",
]


# ---------------------------------------------------------------------------
# Schedule-based stats
# ---------------------------------------------------------------------------

def stats_from_schedules(sched: pd.DataFrame, season: int) -> dict:
    """
    Derive season record and scoring from the nflverse games/schedules file.
    Only regular-season games (game_type == 'REG') are counted.
    """
    reg  = sched[(sched["season"] == season) & (sched["game_type"] == "REG")]
    home = reg[reg["home_team"] == TEAM]
    away = reg[reg["away_team"] == TEAM]

    wins   = int(
        (home["home_score"] > home["away_score"]).sum() +
        (away["away_score"] > away["home_score"]).sum()
    )
    losses = int(
        (home["home_score"] < home["away_score"]).sum() +
        (away["away_score"] < away["home_score"]).sum()
    )
    # Ties: final score is equal (rare but valid in NFL)
    ties = int(
        (home["home_score"] == home["away_score"]).sum() +
        (away["away_score"] == away["home_score"]).sum()
    )

    pf = int(home["home_score"].sum() + away["away_score"].sum())
    pa = int(home["away_score"].sum() + away["home_score"].sum())
    gp = wins + losses + ties

    return {
        "Wins":               wins,
        "Losses":             losses,
        "Ties":               ties,
        "Points_For":         pf,
        "Points_Against":     pa,
        "Point_Differential": pf - pa,
        "Games_Played":       gp,
    }


# ---------------------------------------------------------------------------
# PBP-based stats
# ---------------------------------------------------------------------------

def stats_from_pbp(pbp: pd.DataFrame) -> dict:
    """
    Derive offense and turnover stats from one season's play-by-play data.
    Caller is responsible for pre-filtering to regular-season plays only.

    Definitions used:
      Passing_Yards   — net yards on all passing plays (sack yardage is negative,
                        consistent with how the NFL counts team passing totals)
      Rushing_Yards   — net yards on all rushing plays
      Passing_TDs     — plays where pass_touchdown == 1 and Bears are on offense
      Rushing_TDs     — plays where rush_touchdown == 1 and Bears are on offense
      Total_TDs       — Passing_TDs + Rushing_TDs + defensive/ST TDs
                        (return_touchdown == 1 while Bears are on defense covers
                        pick-6s, fumble-return TDs, and kick/punt-return TDs)
      Turnovers       — interceptions thrown + fumbles lost by Bears offense
      Takeaways       — interceptions + fumble recoveries by Bears defense
                        (fumble_lost == 1 while defteam == CHI means the opposing
                        offense lost possession to CHI)
    """
    # --- Offense: plays where Bears have possession ---
    off = pbp[pbp["posteam"] == TEAM]

    passing_yards = int(
        off.loc[off["play_type"] == "pass", "passing_yards"].sum()
    )
    rushing_yards = int(
        off.loc[off["play_type"] == "run", "rushing_yards"].sum()
    )
    total_offense = passing_yards + rushing_yards

    passing_tds = int(off["pass_touchdown"].sum())
    rushing_tds = int(off["rush_touchdown"].sum())

    # Defensive / special-teams TDs: Bears scored while they were on defense
    # (pick-6, fumble return TD, kick/punt return TD — all tagged as return_touchdown
    # on plays where CHI is defteam)
    def_st_tds = int(pbp.loc[pbp["defteam"] == TEAM, "return_touchdown"].sum())

    total_tds = passing_tds + rushing_tds + def_st_tds

    # Turnovers committed by Bears offense
    turnovers = int(off["interception"].sum() + off["fumble_lost"].sum())

    # Takeaways by Bears defense
    # interception == 1 when defteam == CHI  →  Bears picked off the QB
    # fumble_lost  == 1 when defteam == CHI  →  opponent lost fumble to Bears
    def_plays = pbp[pbp["defteam"] == TEAM]
    takeaways = int(def_plays["interception"].sum() + def_plays["fumble_lost"].sum())

    return {
        "Passing_Yards":         passing_yards,
        "Rushing_Yards":         rushing_yards,
        "Total_Offense_Yards":   total_offense,
        "Passing_TDs":           passing_tds,
        "Rushing_TDs":           rushing_tds,
        "Total_TDs":             total_tds,
        "Turnovers":             turnovers,
        "Takeaways":             takeaways,
        "Turnover_Differential": takeaways - turnovers,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    os.makedirs(SEASON_DIR, exist_ok=True)
    os.makedirs(CLEAN_DIR,  exist_ok=True)

    # --- Load schedules ---
    sched_path = os.path.join(CACHE_DIR, "schedules.csv")
    if not os.path.exists(sched_path):
        sys.exit(
            f"Schedule file not found:\n  {sched_path}\n"
            "Run download_team_stats.py first."
        )
    print("Loading schedules.csv ...", end=" ", flush=True)
    sched = pd.read_csv(sched_path, low_memory=False)
    print(f"{len(sched):,} rows")

    # --- Process each season ---
    all_rows = []

    for season in SEASONS:
        pbp_path = os.path.join(CACHE_DIR, f"pbp_{season}.csv.gz")

        if not os.path.exists(pbp_path):
            print(f"  {season}: PBP file missing ({pbp_path}) — skipping.")
            continue

        print(f"Processing {season} ...", end=" ", flush=True)
        try:
            # Load only the columns we need (much faster than reading all ~370)
            pbp_full = pd.read_csv(
                pbp_path,
                usecols=lambda c: c in LOAD_COLS,
                low_memory=False,
            )

            # Verify required columns are present before computing
            missing = set(LOAD_COLS) - set(pbp_full.columns)
            if missing:
                print(f"SKIP — missing columns: {missing}")
                continue

            # Regular-season plays only
            pbp_reg = pbp_full[pbp_full["season_type"] == "REG"]

            record  = stats_from_schedules(sched, season)
            offense = stats_from_pbp(pbp_reg)

            row = {"Season": season, **record, **offense}

            # Save individual season CSV
            out_path = os.path.join(SEASON_DIR, f"bears_team_stats_{season}.csv")
            pd.DataFrame([row]).to_csv(out_path, index=False)

            all_rows.append(row)
            w, l, t = row["Wins"], row["Losses"], row["Ties"]
            pf, pa  = row["Points_For"], row["Points_Against"]
            print(f"{w}-{l}-{t}  PF:{pf}  PA:{pa}  -> saved")

        except Exception as exc:
            print(f"ERROR: {exc}")

    # --- Save master file ---
    print()
    if not all_rows:
        print("No seasons processed — master file not written.")
        return

    master = (
        pd.DataFrame(all_rows)
          .sort_values("Season")
          .reset_index(drop=True)
    )
    master_path = os.path.join(CLEAN_DIR, "bears_team_stats_2016_2025.csv")
    master.to_csv(master_path, index=False)

    print(f"Master file -> {master_path}")
    print()
    print(master.to_string(index=False))


if __name__ == "__main__":
    main()
