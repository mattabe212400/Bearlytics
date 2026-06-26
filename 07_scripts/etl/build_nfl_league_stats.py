#!/usr/bin/env python3
"""
build_nfl_league_stats.py

Builds a league-wide season statistics table for every NFL team from
2016 through 2025 using the pre-downloaded nflverse cache files.

Does NOT download anything — run download_team_stats.py first.

Input (must already exist):
  01_raw_data/_cache/schedules.csv
  01_raw_data/_cache/pbp_{year}.csv.gz   (2016 through 2025)

Output:
  01_raw_data/league_stats/nfl_league_stats_{year}.csv   — one file per season
  03_clean_data/nfl_league_stats_2016_2025.csv            — combined master file

Column sources:
  FROM schedules.csv  : Wins, Losses, Ties, Win_Percentage,
                        Points_For, Points_Against, Point_Differential
  FROM pbp_{year}.csv : Passing_Yards, Rushing_Yards, Total_Offense_Yards,
                        Passing_TDs, Rushing_TDs, Turnovers, Takeaways,
                        Turnover_Differential, Offensive_Rank, Defensive_Rank

Team-code note:
  The schedules file uses historical abbreviations for franchises that relocated
  (e.g. 'OAK' for the Raiders in 2016–2019, 'SD' for the Chargers in 2016).
  The PBP files use the modern abbreviations retroactively ('LV', 'LAC').
  This script normalizes the schedules codes to match PBP before merging.
  Mapping: OAK → LV,  SD → LAC

Ranking note:
  Offensive_Rank  — 1 = most total offense yards in the league that season
  Defensive_Rank  — 1 = fewest total yards allowed in the league that season
"""

import os
import sys

import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SEASONS = list(range(2016, 2026))   # 2016 through 2025 inclusive

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR    = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "01_raw_data", "_cache"))
LEAGUE_DIR   = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "01_raw_data", "league_stats"))
CLEAN_DIR    = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "03_clean_data"))

# Columns needed from the PBP files (avoids loading all ~370 columns)
PBP_COLS = [
    "season_type",
    "posteam",
    "defteam",
    "play_type",
    "passing_yards",
    "rushing_yards",
    "pass_touchdown",
    "rush_touchdown",
    "interception",
    "fumble_lost",
]

# Schedules use historical team codes for relocated franchises; PBP files use
# the modern/current abbreviations retroactively.  Normalize schedules → PBP.
TEAM_RENAMES = {
    "OAK": "LV",    # Oakland Raiders became Las Vegas Raiders in 2020
    "SD":  "LAC",   # San Diego Chargers became LA Chargers in 2017
}

# Final column order
OUTPUT_COLS = [
    "Season", "Team",
    "Wins", "Losses", "Ties", "Win_Percentage",
    "Points_For", "Points_Against", "Point_Differential",
    "Passing_Yards", "Rushing_Yards", "Total_Offense_Yards",
    "Passing_TDs", "Rushing_TDs",
    "Turnovers", "Takeaways", "Turnover_Differential",
    "Offensive_Rank", "Defensive_Rank",
]


# ---------------------------------------------------------------------------
# Schedule-based stats — all teams at once
# ---------------------------------------------------------------------------

def record_all_teams(sched: pd.DataFrame, season: int) -> pd.DataFrame:
    """
    Return a DataFrame with one row per team containing their season record
    and scoring totals, derived from the schedules file.

    Strategy:
      For each regular-season game, create one row from the home team's
      perspective and one from the away team's perspective, then groupby team.
    """
    reg = sched[(sched["season"] == season) & (sched["game_type"] == "REG")]

    # Drop games without a final score (not yet played)
    reg = reg.dropna(subset=["home_score", "away_score"])

    # Apply team-code normalization so codes match PBP abbreviations
    reg = reg.copy()
    reg["home_team"] = reg["home_team"].replace(TEAM_RENAMES)
    reg["away_team"] = reg["away_team"].replace(TEAM_RENAMES)

    # Build a team-centric view: two rows per game (one per side)
    home = reg[["home_team", "home_score", "away_score"]].copy()
    home.columns = ["team", "pf", "pa"]

    away = reg[["away_team", "away_score", "home_score"]].copy()
    away.columns = ["team", "pf", "pa"]

    games = pd.concat([home, away], ignore_index=True)

    # Compute aggregated record and scoring
    record = (
        games.groupby("team")
        .apply(
            lambda g: pd.Series({
                "Wins":            int((g["pf"] > g["pa"]).sum()),
                "Losses":          int((g["pf"] < g["pa"]).sum()),
                "Ties":            int((g["pf"] == g["pa"]).sum()),
                "Points_For":      int(g["pf"].sum()),
                "Points_Against":  int(g["pa"].sum()),
            })
        )
        .reset_index()
    )

    games_played = record["Wins"] + record["Losses"] + record["Ties"]
    record["Win_Percentage"]     = (record["Wins"] / games_played).round(3)
    record["Point_Differential"] = record["Points_For"] - record["Points_Against"]

    return record


# ---------------------------------------------------------------------------
# PBP-based stats — all teams at once
# ---------------------------------------------------------------------------

def pbp_all_teams(pbp: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate offensive and defensive stats for every team from one season's
    play-by-play data.  The dataframe should already be filtered to regular
    season plays only.

    All groupby operations run over the entire league at once — no per-team loop.
    """
    scrimmage = pbp[pbp["play_type"].isin(["pass", "run"])]
    pass_plays = scrimmage[scrimmage["play_type"] == "pass"]
    run_plays  = scrimmage[scrimmage["play_type"] == "run"]

    # --- Offensive stats (grouped by possession team) ---
    pass_yards = (
        pass_plays.groupby("posteam")["passing_yards"].sum().rename("Passing_Yards")
    )
    rush_yards = (
        run_plays.groupby("posteam")["rushing_yards"].sum().rename("Rushing_Yards")
    )
    pass_tds = (
        scrimmage.groupby("posteam")["pass_touchdown"].sum().rename("Passing_TDs")
    )
    rush_tds = (
        scrimmage.groupby("posteam")["rush_touchdown"].sum().rename("Rushing_TDs")
    )
    # Turnovers = interceptions thrown + fumbles lost by the offense
    turnovers = (
        scrimmage.groupby("posteam")["interception"].sum()
        + scrimmage.groupby("posteam")["fumble_lost"].sum()
    ).rename("Turnovers")

    off = pd.concat(
        [pass_yards, rush_yards, pass_tds, rush_tds, turnovers], axis=1
    ).reset_index().rename(columns={"posteam": "team"})

    off["Total_Offense_Yards"] = off["Passing_Yards"] + off["Rushing_Yards"]

    # --- Defensive stats (grouped by defending team) ---
    # Takeaways = interceptions by defense + fumbles recovered from opponent
    #   interception == 1  when defteam == team  →  defense picked off the QB
    #   fumble_lost  == 1  when defteam == team  →  defense recovered the fumble
    takeaways = (
        pass_plays.groupby("defteam")["interception"].sum()
        + scrimmage.groupby("defteam")["fumble_lost"].sum()
    ).rename("Takeaways").reset_index().rename(columns={"defteam": "team"})

    # Total yards allowed (used to compute Defensive_Rank; not an output column)
    def_yards_allowed = (
        pass_plays.groupby("defteam")["passing_yards"].sum()
        + run_plays.groupby("defteam")["rushing_yards"].sum()
    ).rename("_def_yards").reset_index().rename(columns={"defteam": "team"})

    # --- Merge offense + defense ---
    stats = (
        off
        .merge(takeaways,        on="team", how="outer")
        .merge(def_yards_allowed, on="team", how="outer")
    )

    # Fill numeric NaN with 0 (a team absent from a category has 0, not unknown)
    numeric_cols = [
        "Passing_Yards", "Rushing_Yards", "Total_Offense_Yards",
        "Passing_TDs", "Rushing_TDs", "Turnovers", "Takeaways", "_def_yards",
    ]
    stats[numeric_cols] = stats[numeric_cols].fillna(0).astype(int)

    stats["Turnover_Differential"] = stats["Takeaways"] - stats["Turnovers"]

    # --- Rankings ---
    # Offensive_Rank: more total offense yards = better (rank 1)
    stats["Offensive_Rank"] = (
        stats["Total_Offense_Yards"]
        .rank(ascending=False, method="min")
        .astype(int)
    )
    # Defensive_Rank: fewer yards allowed = better (rank 1)
    stats["Defensive_Rank"] = (
        stats["_def_yards"]
        .rank(ascending=True, method="min")
        .astype(int)
    )

    # Drop internal helper column
    stats = stats.drop(columns=["_def_yards"])

    return stats


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    os.makedirs(LEAGUE_DIR, exist_ok=True)
    os.makedirs(CLEAN_DIR,  exist_ok=True)

    # --- Load schedule file (small, load once) ---
    sched_path = os.path.join(CACHE_DIR, "schedules.csv")
    if not os.path.exists(sched_path):
        sys.exit(
            f"Schedule file not found:\n  {sched_path}\n"
            "Run download_team_stats.py first."
        )

    print("Loading schedules.csv ...", end=" ", flush=True)
    sched = pd.read_csv(sched_path, low_memory=False)
    print(f"{len(sched):,} rows\n")

    all_seasons = []

    for season in SEASONS:
        pbp_path = os.path.join(CACHE_DIR, f"pbp_{season}.csv.gz")

        if not os.path.exists(pbp_path):
            print(f"  {season}: PBP file missing — skipping.")
            continue

        print(f"Processing {season} ...", end=" ", flush=True)
        try:
            # Load only the columns this script needs
            pbp_full = pd.read_csv(
                pbp_path,
                usecols=lambda c: c in PBP_COLS,
                low_memory=False,
            )

            # Verify required columns are present
            missing = set(PBP_COLS) - set(pbp_full.columns)
            if missing:
                print(f"SKIP — missing PBP columns: {missing}")
                continue

            # Regular season only
            pbp_reg = pbp_full[pbp_full["season_type"] == "REG"]

            # Build stats
            record = record_all_teams(sched, season)
            pbp_stats = pbp_all_teams(pbp_reg)

            # Merge schedule record + PBP stats on team code
            season_df = record.merge(pbp_stats, on="team", how="outer")
            season_df.insert(0, "Season", season)
            season_df = season_df.rename(columns={"team": "Team"})

            # Enforce output column order; fill any gap columns with empty string
            for col in OUTPUT_COLS:
                if col not in season_df.columns:
                    season_df[col] = ""
            season_df = season_df[OUTPUT_COLS]

            # Sort by Offensive_Rank so the strongest offenses appear first
            season_df = season_df.sort_values("Offensive_Rank").reset_index(drop=True)

            # Save per-season file
            out_path = os.path.join(LEAGUE_DIR, f"nfl_league_stats_{season}.csv")
            season_df.to_csv(out_path, index=False)

            all_seasons.append(season_df)
            print(f"{len(season_df)} teams  ->  {os.path.basename(out_path)}")

        except Exception as exc:
            print(f"ERROR: {exc}")

    # --- Save master file ---
    print()
    if not all_seasons:
        print("No seasons processed — master file not written.")
        return

    master = (
        pd.concat(all_seasons, ignore_index=True)
        .sort_values(["Season", "Offensive_Rank"])
        .reset_index(drop=True)
    )
    master_path = os.path.join(CLEAN_DIR, "nfl_league_stats_2016_2025.csv")
    master.to_csv(master_path, index=False)

    print(f"Master file  ->  {master_path}")
    print(f"Total rows   :  {len(master):,}  "
          f"({master['Season'].nunique()} seasons × ~{len(master) // master['Season'].nunique()} teams)")


if __name__ == "__main__":
    main()
