#!/usr/bin/env python3
"""
build_bears_player_stats.py

Aggregates Chicago Bears individual player statistics for every regular-season
game from 2016 through 2025 using the pre-downloaded nflverse PBP files.

Does NOT download anything — run download_team_stats.py first.

Input:
  01_raw_data/_cache/pbp_{year}.csv.gz   (2016 through 2025)

Output:
  01_raw_data/player_stats/bears_player_stats_{year}.csv   — one per season
  03_clean_data/bears_player_stats_2016_2025.csv            — combined master

Column notes:
  Position     — LEFT BLANK intentionally. Play-by-play data records player
                 roles (passer / rusher / receiver) but not roster positions.
                 A QB scramble appears under rusher_player_name, same as a RB
                 carry, making reliable position inference impossible without a
                 separate roster file. Use build_roster.py (future script) to
                 join positions in.

  Games_Played — count of distinct game_id values where the player appears in
                 any offensive role (passing, rushing, or receiving) during the
                 regular season.

  Targets      — pass plays where receiver_player_name is not null.
                 nflverse sets this on targeted pass attempts (complete AND
                 incomplete), but roughly 35% of incomplete passes have no
                 receiver name (typically scrambles or plays without a
                 clear intended target). Those untargeted plays do not inflate
                 any player's target count.

  Receiving_Yards  — sum of receiving_yards on completed targets only; NaN rows
                     (incomplete passes, interceptions) contribute 0 via pandas
                     sum() default behavior.

  Passing_Yards    — sum of passing_yards on pass plays; sack plays show NaN
                     in passing_yards so sack losses do not reduce this total,
                     consistent with how the NFL tracks individual QB passing
                     yards (sack yardage is a team-level penalty, not charged
                     to the QB's passing total).

  Total_Yards  — Passing_Yards + Rushing_Yards + Receiving_Yards
  Total_TDs    — Passing_TDs  + Rushing_TDs  + Receiving_TDs
"""

import os
import sys

import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TEAM    = "CHI"
SEASONS = list(range(2016, 2026))

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR   = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "01_raw_data", "_cache"))
PLAYER_DIR  = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "01_raw_data", "player_stats"))
CLEAN_DIR   = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "03_clean_data"))

# Only load the columns this script needs (avoids pulling all ~370 columns)
LOAD_COLS = [
    "season_type",
    "game_id",
    "posteam",
    "play_type",
    # Passing
    "passer_player_name",
    "passing_yards",
    "pass_touchdown",
    "interception",
    # Rushing
    "rusher_player_name",
    "rushing_yards",
    "rush_touchdown",
    # Receiving
    "receiver_player_name",
    "receiving_yards",
    "complete_pass",
]


# ---------------------------------------------------------------------------
# Per-category aggregation helpers
# ---------------------------------------------------------------------------

def passing_stats(pbp: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate QB stats for all passers.
    Filters to plays where passer_player_name is not null (actual pass attempts,
    including sacks; kneel-downs and spikes have no passer name).
    """
    passes = pbp[pbp["passer_player_name"].notna()].copy()

    agg = (
        passes.groupby("passer_player_name")
        .agg(
            Passing_Yards       = ("passing_yards",  "sum"),   # NaN sacks → 0
            Passing_TDs         = ("pass_touchdown",  "sum"),
            Interceptions_Thrown= ("interception",    "sum"),
        )
        .reset_index()
        .rename(columns={"passer_player_name": "Player_Name"})
    )
    return agg


def rushing_stats(pbp: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate rushing stats for all ball-carriers.
    Filters to run plays with a named rusher (excludes kneel-downs, which
    also appear as play_type == 'run' but typically have a rusher name set
    with 0 or negative yards — these are included as they count in official
    stats).
    """
    runs = pbp[(pbp["play_type"] == "run") & pbp["rusher_player_name"].notna()].copy()

    agg = (
        runs.groupby("rusher_player_name")
        .agg(
            Rushing_Yards = ("rushing_yards",  "sum"),
            Rushing_TDs   = ("rush_touchdown", "sum"),
        )
        .reset_index()
        .rename(columns={"rusher_player_name": "Player_Name"})
    )
    return agg


def receiving_stats(pbp: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate receiving stats for all targeted receivers.

    Targets  = any pass play where receiver_player_name is not null.
               (~35% of incomplete passes lack a receiver name and are excluded;
               see module docstring for details.)

    Receptions = targets where complete_pass == 1.

    Receiving_TDs = pass_touchdown == 1 on plays where the player is receiver.
                   (On a pass TD, nflverse sets receiver_player_name to the
                   player who caught it, so this correctly assigns TDs.)
    """
    # All targeted passes (complete + incomplete)
    targeted = pbp[pbp["receiver_player_name"].notna()].copy()

    targets = (
        targeted.groupby("receiver_player_name")
        .size()
        .reset_index(name="Targets")
    )

    # Completed passes only
    completed = targeted[targeted["complete_pass"] == 1]
    receptions = (
        completed.groupby("receiver_player_name")
        .size()
        .reset_index(name="Receptions")
    )

    recv_yards = (
        completed.groupby("receiver_player_name")
        .agg(
            Receiving_Yards = ("receiving_yards", "sum"),
            Receiving_TDs   = ("pass_touchdown",  "sum"),
        )
        .reset_index()
    )

    agg = (
        targets
        .merge(receptions, on="receiver_player_name", how="left")
        .merge(recv_yards,  on="receiver_player_name", how="left")
        .rename(columns={"receiver_player_name": "Player_Name"})
    )
    return agg


def games_played(pbp: pd.DataFrame) -> pd.DataFrame:
    """
    Count distinct game_id values per player across all offensive roles.
    A player is counted in a game if they appear in any play as passer,
    rusher, or targeted receiver.
    """
    passer_games = (
        pbp[pbp["passer_player_name"].notna()][["passer_player_name", "game_id"]]
        .rename(columns={"passer_player_name": "Player_Name"})
    )
    rusher_games = (
        pbp[(pbp["play_type"] == "run") & pbp["rusher_player_name"].notna()]
        [["rusher_player_name", "game_id"]]
        .rename(columns={"rusher_player_name": "Player_Name"})
    )
    receiver_games = (
        pbp[pbp["receiver_player_name"].notna()][["receiver_player_name", "game_id"]]
        .rename(columns={"receiver_player_name": "Player_Name"})
    )

    all_appearances = pd.concat(
        [passer_games, rusher_games, receiver_games],
        ignore_index=True
    ).drop_duplicates()

    gp = (
        all_appearances.groupby("Player_Name")["game_id"]
        .nunique()
        .reset_index(name="Games_Played")
    )
    return gp


# ---------------------------------------------------------------------------
# Season builder
# ---------------------------------------------------------------------------

def build_season(pbp_path: str, season: int) -> pd.DataFrame | None:
    """
    Load one season's PBP file, filter to Bears regular-season offensive plays,
    and return a player-season stats DataFrame.
    Returns None if the file is missing or an error occurs.
    """
    if not os.path.exists(pbp_path):
        print(f"  {season}: file not found — skipping.")
        return None

    print(f"  Loading {os.path.basename(pbp_path)} ...", end=" ", flush=True)
    try:
        pbp_full = pd.read_csv(
            pbp_path,
            usecols=lambda c: c in LOAD_COLS,
            low_memory=False,
        )
    except Exception as exc:
        print(f"READ ERROR: {exc}")
        return None

    # Regular season, Bears on offense
    pbp = pbp_full[
        (pbp_full["season_type"] == "REG") &
        (pbp_full["posteam"] == TEAM)
    ].copy()

    print(f"{len(pbp):,} Bears offensive plays", end=" ")

    # Verify minimum required columns exist before proceeding
    required = {"passer_player_name", "rusher_player_name", "receiver_player_name",
                "passing_yards", "rushing_yards", "receiving_yards",
                "pass_touchdown", "rush_touchdown", "complete_pass", "game_id"}
    missing = required - set(pbp.columns)
    if missing:
        print(f"SKIP — missing columns: {missing}")
        return None

    # Compute each stat category
    pass_df = passing_stats(pbp)
    rush_df = rushing_stats(pbp)
    recv_df = receiving_stats(pbp)
    gp_df   = games_played(pbp)

    # Outer-join all categories so a player with only rushing stats
    # still appears with NaN in passing/receiving columns
    merged = (
        pass_df
        .merge(rush_df, on="Player_Name", how="outer")
        .merge(recv_df, on="Player_Name", how="outer")
        .merge(gp_df,   on="Player_Name", how="outer")
    )

    # Fill missing numeric stats with 0 (a player without passing stats has 0
    # passing yards, not an unknown value)
    numeric_cols = [
        "Passing_Yards", "Passing_TDs", "Interceptions_Thrown",
        "Rushing_Yards", "Rushing_TDs",
        "Receiving_Yards", "Receiving_TDs", "Receptions", "Targets",
        "Games_Played",
    ]
    for col in numeric_cols:
        if col in merged.columns:
            merged[col] = merged[col].fillna(0).astype(int)

    # Derived totals
    merged["Total_Yards"] = (
        merged["Passing_Yards"] +
        merged["Rushing_Yards"] +
        merged["Receiving_Yards"]
    )
    merged["Total_TDs"] = (
        merged["Passing_TDs"] +
        merged["Rushing_TDs"] +
        merged["Receiving_TDs"]
    )

    # Add season-level metadata
    merged.insert(0, "Season", season)
    merged.insert(2, "Position", "")   # not derivable from PBP — see module docstring
    merged.insert(3, "Team", TEAM)

    # Sort by Total_Yards descending so top contributors appear first
    merged = merged.sort_values("Total_Yards", ascending=False).reset_index(drop=True)

    print(f"→ {len(merged)} players")
    return merged


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    os.makedirs(PLAYER_DIR, exist_ok=True)
    os.makedirs(CLEAN_DIR,  exist_ok=True)

    print(f"Building Bears player stats 2016–2025\n")

    all_seasons = []

    for season in SEASONS:
        pbp_path = os.path.join(CACHE_DIR, f"pbp_{season}.csv.gz")
        df = build_season(pbp_path, season)

        if df is None:
            continue

        # Save per-season file
        out_path = os.path.join(PLAYER_DIR, f"bears_player_stats_{season}.csv")
        df.to_csv(out_path, index=False)
        all_seasons.append(df)

    if not all_seasons:
        print("No seasons processed — no files written.")
        return

    # --- Save master file ---
    master = pd.concat(all_seasons, ignore_index=True)
    master_path = os.path.join(CLEAN_DIR, "bears_player_stats_2016_2025.csv")
    master.to_csv(master_path, index=False)

    print(f"\nMaster file → {master_path}")
    print(f"Total rows : {len(master):,}  ({master['Season'].nunique()} seasons, "
          f"{master['Player_Name'].nunique()} unique player names)")


if __name__ == "__main__":
    main()
