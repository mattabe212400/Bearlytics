#!/usr/bin/env python3
"""
build_bears_game_logs.py

Builds a game-by-game log for every Chicago Bears regular-season game
from 2016 through 2025 using the pre-downloaded nflverse schedules file.

Does NOT download anything — run download_team_stats.py first.

Input:
  01_raw_data/_cache/schedules.csv

Output:
  01_raw_data/game_logs/bears_game_log_{year}.csv   — one file per season
  03_clean_data/bears_game_logs_2016_2025.csv        — combined master file

Column notes:
  Home_Away          — "Home" if Bears are the home team, "Away" otherwise
  Result             — "W", "L", or "T" from the Bears' perspective
  Point_Differential — Points_For minus Points_Against (negative = loss)
  Wins/Losses/Ties_After_Game — running season record through that game,
                                 sorted by week ascending
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
LOGS_DIR   = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "01_raw_data", "game_logs"))
CLEAN_DIR  = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "03_clean_data"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def reshape_game(row: pd.Series) -> dict:
    """
    Convert one row from the schedules file into a Bears-centric game record.

    nflverse's `result` column is always from the HOME team's perspective:
      result > 0  →  home team won
      result < 0  →  away team won
      result == 0 →  tie

    Points and W/L/T are flipped for the Bears when they are the away team.
    """
    bears_are_home = row["home_team"] == TEAM

    if bears_are_home:
        opponent = row["away_team"]
        pf       = row["home_score"]
        pa       = row["away_score"]
        # result > 0 means home (Bears) won
        if row["result"] > 0:
            result = "W"
        elif row["result"] < 0:
            result = "L"
        else:
            result = "T"
    else:
        opponent = row["home_team"]
        pf       = row["away_score"]
        pa       = row["home_score"]
        # result < 0 means away team (Bears) won
        if row["result"] < 0:
            result = "W"
        elif row["result"] > 0:
            result = "L"
        else:
            result = "T"

    return {
        "Season":             int(row["season"]),
        "Week":               int(row["week"]),
        "Game_Date":          row["gameday"],
        "Opponent":           opponent,
        "Home_Away":          "Home" if bears_are_home else "Away",
        "Result":             result,
        "Points_For":         int(pf),
        "Points_Against":     int(pa),
        "Point_Differential": int(pf - pa),
    }


def add_running_record(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add cumulative Wins_After_Game, Losses_After_Game, Ties_After_Game columns.
    Rows must already be sorted by Week (ascending) within a single season.
    """
    df = df.copy()
    df["Wins_After_Game"]   = (df["Result"] == "W").cumsum()
    df["Losses_After_Game"] = (df["Result"] == "L").cumsum()
    df["Ties_After_Game"]   = (df["Result"] == "T").cumsum()
    return df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    os.makedirs(LOGS_DIR,  exist_ok=True)
    os.makedirs(CLEAN_DIR, exist_ok=True)

    # --- Load schedule file ---
    sched_path = os.path.join(CACHE_DIR, "schedules.csv")
    if not os.path.exists(sched_path):
        sys.exit(
            f"Schedule file not found:\n  {sched_path}\n"
            "Run download_team_stats.py first."
        )

    print(f"Loading schedules.csv ...", end=" ", flush=True)
    sched = pd.read_csv(sched_path, low_memory=False)
    print(f"{len(sched):,} rows")

    # --- Filter to Bears regular-season games in target seasons ---
    bears_mask = (
        ((sched["home_team"] == TEAM) | (sched["away_team"] == TEAM)) &
        (sched["game_type"] == "REG") &
        (sched["season"].isin(SEASONS))
    )
    bears_games = sched[bears_mask].copy()

    # Drop any games without a final score (e.g. scheduled but not yet played)
    bears_games = bears_games.dropna(subset=["home_score", "away_score", "result"])

    print(f"Bears regular-season games found: {len(bears_games)}\n")

    # --- Build game log rows ---
    rows = [reshape_game(row) for _, row in bears_games.iterrows()]
    game_log = pd.DataFrame(rows)

    # --- Process each season individually ---
    all_seasons = []

    for season in sorted(game_log["Season"].unique()):
        season_df = (
            game_log[game_log["Season"] == season]
            .sort_values("Week")
            .reset_index(drop=True)
        )

        season_df = add_running_record(season_df)

        # Save per-season file
        out_path = os.path.join(LOGS_DIR, f"bears_game_log_{season}.csv")
        season_df.to_csv(out_path, index=False)

        final_w = season_df["Wins_After_Game"].iloc[-1]
        final_l = season_df["Losses_After_Game"].iloc[-1]
        final_t = season_df["Ties_After_Game"].iloc[-1]
        print(f"  {season}: {len(season_df)} games  |  final record {final_w}-{final_l}-{final_t}  ->  {os.path.basename(out_path)}")

        all_seasons.append(season_df)

    # --- Save master file ---
    master = pd.concat(all_seasons, ignore_index=True)
    master_path = os.path.join(CLEAN_DIR, "bears_game_logs_2016_2025.csv")
    master.to_csv(master_path, index=False)

    print(f"\nMaster file -> {master_path}")
    print(f"Total rows: {len(master)}")


if __name__ == "__main__":
    main()
