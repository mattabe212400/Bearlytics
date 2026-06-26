#!/usr/bin/env python3
"""
download_team_stats.py

Downloads Chicago Bears team statistics for seasons 2016-2025 directly
from the nflverse open-source dataset (GitHub releases).

No nfl_data_py required — only requests and pandas.

Data sources:
  - nflverse schedules.csv      ->  Wins, Losses, Points For, Points Against
  - nflverse play_by_play_YYYY  ->  Passing/Rushing Yards, Total Offense/Defense,
                                    Turnovers, Third Down %, Red Zone %,
                                    Offensive Rank, Defensive Rank

Output:
  01_raw_data/team_stats/bears_team_stats_YYYY.csv   (one file per season)

PBP files are cached in 01_raw_data/_cache/ so re-runs skip the download.

Setup:
  pip install requests pandas
"""

import os
import sys

import pandas as pd

try:
    import requests
except ImportError:
    sys.exit("requests is not installed. Run: pip install requests pandas")

try:
    import pandas as pd
except ImportError:
    sys.exit("pandas is not installed. Run: pip install requests pandas")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TEAM    = "CHI"
SEASONS = list(range(2016, 2026))   # 2016 through 2025 inclusive

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "01_raw_data", "team_stats"))
CACHE_DIR  = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "01_raw_data", "_cache"))

SCHEDULES_URL    = "https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv"
PBP_URL_TEMPLATE = "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{year}.csv.gz"

# Only read the PBP columns we actually need (keeps memory usage low)
PBP_COLS = {
    "season", "season_type", "posteam", "defteam", "play_type",
    "passing_yards", "rushing_yards", "down", "yardline_100",
    "first_down", "touchdown", "interception", "fumble_lost",
}


# ---------------------------------------------------------------------------
# Download helpers
# ---------------------------------------------------------------------------

def download_with_progress(url, dest_path):
    """Download a file to dest_path, showing MB progress."""
    print(f"  Downloading {os.path.basename(dest_path)} ...", end=" ", flush=True)
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Download failed for {url}: {exc}")

    total = int(response.headers.get("content-length", 0))
    downloaded = 0

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=65536):
            f.write(chunk)
            downloaded += len(chunk)
            if total > 0:
                print(
                    f"\r  Downloading {os.path.basename(dest_path)} ... "
                    f"{downloaded / 1e6:.1f}/{total / 1e6:.1f} MB",
                    end="", flush=True,
                )
    print(" done.")


def fetch_schedules():
    """Load full schedule data; use cache if available."""
    cache_path = os.path.join(CACHE_DIR, "schedules.csv")
    if not os.path.exists(cache_path):
        download_with_progress(SCHEDULES_URL, cache_path)
    else:
        print("  Schedules: using cached file.")
    return pd.read_csv(cache_path, low_memory=False)


def fetch_pbp(year):
    """Load play-by-play for one season; download and cache if needed."""
    cache_path = os.path.join(CACHE_DIR, f"pbp_{year}.csv.gz")
    url = PBP_URL_TEMPLATE.format(year=year)
    if not os.path.exists(cache_path):
        download_with_progress(url, cache_path)
    else:
        print(f"  PBP {year}: using cached file.")
    # Load only the columns we need
    return pd.read_csv(cache_path, usecols=lambda c: c in PBP_COLS, low_memory=False)


# ---------------------------------------------------------------------------
# Stat-computation helpers
# ---------------------------------------------------------------------------

def get_record(sched, season):
    """Return wins, losses, points for, and points against for the Bears."""
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
    pf = int(home["home_score"].sum() + away["away_score"].sum())
    pa = int(home["away_score"].sum() + away["home_score"].sum())

    return {"Wins": wins, "Losses": losses, "Points_For": pf, "Points_Against": pa}


def get_offense_stats(pbp, team):
    """
    Aggregate offensive stats from a single-season PBP dataframe.
    Caller is responsible for pre-filtering to regular season.
    """
    plays = pbp[(pbp["posteam"] == team) & (pbp["play_type"].isin(["pass", "run"]))]

    pass_plays = plays[plays["play_type"] == "pass"]
    run_plays  = plays[plays["play_type"] == "run"]

    pass_yds  = int(pass_plays["passing_yards"].sum())
    rush_yds  = int(run_plays["rushing_yards"].sum())
    total_off = pass_yds + rush_yds
    turnovers = int(plays["interception"].sum() + plays["fumble_lost"].sum())

    # Third-down conversion rate
    third = plays[plays["down"] == 3]
    third_pct = (
        round(third["first_down"].sum() / len(third) * 100, 1)
        if len(third) > 0 else 0.0
    )

    # Red zone: TDs scored / first-down plays inside the opponent's 20.
    # Using "down == 1 inside the 20" as a proxy for distinct RZ trips.
    rz       = plays[plays["yardline_100"] <= 20]
    rz_trips = int((rz["down"] == 1).sum())
    rz_tds   = int(rz["touchdown"].sum())
    rz_pct   = round(rz_tds / rz_trips * 100, 1) if rz_trips > 0 else 0.0

    return {
        "Passing_Yards":  pass_yds,
        "Rushing_Yards":  rush_yds,
        "Total_Offense":  total_off,
        "Turnovers":      turnovers,
        "Third_Down_Pct": third_pct,
        "Red_Zone_Pct":   rz_pct,
    }


def get_total_defense(pbp, team):
    """Total yards allowed by this team's defense."""
    plays = pbp[(pbp["defteam"] == team) & (pbp["play_type"].isin(["pass", "run"]))]
    pass_allowed = int(plays.loc[plays["play_type"] == "pass", "passing_yards"].sum())
    rush_allowed = int(plays.loc[plays["play_type"] == "run",  "rushing_yards"].sum())
    return pass_allowed + rush_allowed


def get_rankings(pbp):
    """
    Rank all teams by total offensive yards (more = rank 1) and
    total defensive yards allowed (fewer = rank 1).
    Returns the Bears' two ranks as integers.
    """
    scrimmage = pbp[pbp["play_type"].isin(["pass", "run"])]

    # Offensive totals per team
    off_pass = scrimmage[scrimmage["play_type"] == "pass"].groupby("posteam")["passing_yards"].sum()
    off_rush = scrimmage[scrimmage["play_type"] == "run"].groupby("posteam")["rushing_yards"].sum()
    off_total = off_pass.add(off_rush, fill_value=0)
    off_ranks = off_total.rank(ascending=False, method="min").astype(int)

    # Defensive totals per team
    def_pass = scrimmage[scrimmage["play_type"] == "pass"].groupby("defteam")["passing_yards"].sum()
    def_rush = scrimmage[scrimmage["play_type"] == "run"].groupby("defteam")["rushing_yards"].sum()
    def_total = def_pass.add(def_rush, fill_value=0)
    def_ranks = def_total.rank(ascending=True, method="min").astype(int)

    off_rank = int(off_ranks[TEAM]) if TEAM in off_ranks.index else None
    def_rank = int(def_ranks[TEAM]) if TEAM in def_ranks.index else None
    return off_rank, def_rank


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR,  exist_ok=True)
    print(f"Output  -> {OUTPUT_DIR}")
    print(f"Cache   -> {CACHE_DIR}\n")

    # Schedules are one combined file — download once
    print("--- Schedules ---")
    try:
        sched = fetch_schedules()
    except Exception as exc:
        sys.exit(f"Could not load schedule data: {exc}")

    print()
    saved = 0
    for season in SEASONS:
        print(f"--- Season {season} ---")
        try:
            # PBP is one file per season
            pbp_full = fetch_pbp(season)

            # Filter to regular season once; reuse for offense, defense, rankings
            pbp_reg = pbp_full[pbp_full["season_type"] == "REG"]

            record    = get_record(sched, season)
            off       = get_offense_stats(pbp_reg, TEAM)
            total_def = get_total_defense(pbp_reg, TEAM)
            off_rank, def_rank = get_rankings(pbp_reg)

            row = {
                "Season":         season,
                "Wins":           record["Wins"],
                "Losses":         record["Losses"],
                "Points_For":     record["Points_For"],
                "Points_Against": record["Points_Against"],
                "Passing_Yards":  off["Passing_Yards"],
                "Rushing_Yards":  off["Rushing_Yards"],
                "Total_Offense":  off["Total_Offense"],
                "Total_Defense":  total_def,
                "Turnovers":      off["Turnovers"],
                "Third_Down_Pct": off["Third_Down_Pct"],
                "Red_Zone_Pct":   off["Red_Zone_Pct"],
                "Offensive_Rank": off_rank,
                "Defensive_Rank": def_rank,
            }

            out_path = os.path.join(OUTPUT_DIR, f"bears_team_stats_{season}.csv")
            pd.DataFrame([row]).to_csv(out_path, index=False)
            print(f"  Saved -> {os.path.basename(out_path)}")
            saved += 1

        except Exception as exc:
            print(f"  ERROR for {season}: {exc}")

        print()

    print(f"Done. {saved}/{len(SEASONS)} season files saved to:")
    print(f"  {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
