#!/usr/bin/env python3
"""
create_dim_players.py

Builds a player dimension table for Power BI by combining unique players from
bears_player_stats_2016_2025.csv and bears_salary_data_2016_2025.csv.

Name format difference:
  player_stats  →  PBP abbreviated  :  "M.Trubisky", "D.Montgomery"
  salary_data   →  full name        :  "Mitchell Trubisky", "David Montgomery"

Deduplication strategy:
  For each salary player, abbreviate their full name to "F.Last" format and
  check whether that abbreviated name already exists in the player_stats roster.
  If it matches → the two records refer to the same person.  The player_stats
  abbreviated name is used as the canonical Player_Name, and the season range
  is extended to cover both datasets.
  If no match → the player only appears in salary data (usually a defensive or
  special-teams player with no offensive PBP stats) and is added with their
  full name and salary-derived position.

Position priority:
  1. player_stats Position  (filled by prior populate scripts)
  2. salary_data  Position  (fallback if player_stats Position is still blank)

Output columns:
  Player_ID        — auto-incrementing integer (1-based, sorted by name)
  Player_Name      — canonical name (abbreviated for offensive players)
  Position         — most common non-blank position across all seasons
  First_Season     — earliest season the player appears in either dataset
  Last_Season      — latest  season the player appears in either dataset

Input:
  03_clean_data/bears_player_stats_2016_2025.csv
  03_clean_data/bears_salary_data_2016_2025.csv

Output:
  03_clean_data/dim_players.csv

Setup:
  pip install pandas
"""

import os
import sys

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
CLEAN_DIR   = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "03_clean_data"))

STATS_FILE  = os.path.join(CLEAN_DIR, "bears_player_stats_2016_2025.csv")
SALARY_FILE = os.path.join(CLEAN_DIR, "bears_salary_data_2016_2025.csv")
OUTPUT_FILE = os.path.join(CLEAN_DIR, "dim_players.csv")

# ---------------------------------------------------------------------------
# Name utilities
# ---------------------------------------------------------------------------

_SUFFIXES = frozenset(["jr", "sr", "ii", "iii", "iv", "v"])


def abbreviate_name(full_name: str) -> str:
    """
    Convert a full player name to PBP abbreviated format.
    "Mitchell Trubisky" → "M.Trubisky"
    "Allen Robinson II" → "A.Robinson"
    Returns the name unchanged if it has fewer than two parts.
    """
    parts = str(full_name).strip().split()
    # Strip trailing suffixes before abbreviating
    while len(parts) > 1 and parts[-1].lower().rstrip(".") in _SUFFIXES:
        parts.pop()
    if len(parts) < 2:
        return str(full_name).strip()
    return f"{parts[0][0].upper()}.{' '.join(parts[1:])}"


def dominant_position(series: pd.Series) -> str:
    """
    Return the most common non-blank position value from a Series.
    Returns an empty string if no valid position exists.
    """
    valid = series.dropna()
    valid = valid[valid.astype(str).str.strip().str.lower().replace("nan", "") != ""]
    if valid.empty:
        return ""
    return str(valid.mode().iloc[0]).strip()


# ---------------------------------------------------------------------------
# Per-dataset summaries
# ---------------------------------------------------------------------------

def summarise_players(df: pd.DataFrame) -> dict:
    """
    Collapse a player dataset into one record per Player_Name.

    Returns a dict keyed by Player_Name:
      {
        "position":     str,
        "first_season": int,
        "last_season":  int,
      }
    """
    summary = {}
    for player_name, group in df.groupby("Player_Name"):
        summary[str(player_name).strip()] = {
            "position":     dominant_position(group["Position"]),
            "first_season": int(group["Season"].min()),
            "last_season":  int(group["Season"].max()),
        }
    return summary


# ---------------------------------------------------------------------------
# Cross-dataset deduplication
# ---------------------------------------------------------------------------

def build_salary_abbrev_map(salary_summary: dict, stats_summary: dict) -> dict:
    """
    For each salary player, attempt to abbreviate their full name.
    If the abbreviation matches an existing player_stats name, record the link.

    Returns a dict:  abbreviated_name → salary_full_name
    Entries where abbreviation is ambiguous (two salary players shorten to the
    same string) are excluded to avoid mis-linking players.
    """
    # Map abbreviated salary name → list of full salary names that produce it
    candidates: dict[str, list] = {}
    for full_name in salary_summary:
        abbrev = abbreviate_name(full_name)
        candidates.setdefault(abbrev, []).append(full_name)

    abbrev_map = {}
    for abbrev, full_names in candidates.items():
        # Only link when the abbreviation uniquely identifies one salary player
        # AND that abbreviation already exists in the player_stats roster
        if len(full_names) == 1 and abbrev in stats_summary:
            abbrev_map[abbrev] = full_names[0]

    return abbrev_map  # {abbrev_name: salary_full_name}


# ---------------------------------------------------------------------------
# Build unified player list
# ---------------------------------------------------------------------------

def build_dim_players(stats_summary: dict, salary_summary: dict) -> pd.DataFrame:
    """
    Merge the two player summaries into a single deduplicated player list.

    For matched players (same person in both datasets):
      - Canonical name  = abbreviated name from player_stats
      - Position        = player_stats position, fallback to salary position
      - Season range    = min/max across both datasets

    For salary-only players (no offensive PBP stats):
      - Canonical name  = full name from salary data
      - Position        = salary position
      - Season range    = from salary data only
    """
    abbrev_map = build_salary_abbrev_map(salary_summary, stats_summary)
    # Invert so we can quickly find which salary full name each abbrev maps to
    matched_salary_full_names = set(abbrev_map.values())

    players = {}

    # --- Player_stats players (always included) ---
    for name, info in stats_summary.items():
        pos          = info["position"]
        first_season = info["first_season"]
        last_season  = info["last_season"]

        # If this abbreviated name maps to a salary player, merge season range
        # and fall back to salary position if player_stats position is blank
        if name in abbrev_map:
            sal_info     = salary_summary[abbrev_map[name]]
            first_season = min(first_season, sal_info["first_season"])
            last_season  = max(last_season,  sal_info["last_season"])
            if not pos:
                pos = sal_info["position"]

        players[name] = {
            "Player_Name":  name,
            "Position":     pos,
            "First_Season": first_season,
            "Last_Season":  last_season,
        }

    # --- Salary-only players (not matched to any player_stats entry) ---
    for full_name, info in salary_summary.items():
        if full_name in matched_salary_full_names:
            continue  # Already merged into a player_stats entry above
        # This player never appeared in offensive PBP (defender, lineman, etc.)
        players[full_name] = {
            "Player_Name":  full_name,
            "Position":     info["position"],
            "First_Season": info["first_season"],
            "Last_Season":  info["last_season"],
        }

    # --- Assemble DataFrame, sort, and add Player_ID ---
    df = (
        pd.DataFrame(players.values())
        .sort_values("Player_Name", key=lambda s: s.str.lower())
        .reset_index(drop=True)
    )
    # Player_ID: 1-based integer, assigned after alphabetical sort
    df.insert(0, "Player_ID", range(1, len(df) + 1))

    return df[["Player_ID", "Player_Name", "Position", "First_Season", "Last_Season"]]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # Verify input files exist
    for path, label in [(STATS_FILE, "player stats"), (SALARY_FILE, "salary data")]:
        if not os.path.exists(path):
            sys.exit(f"File not found: {path}  ({label})")

    # Load datasets
    print("Loading datasets ...", end=" ", flush=True)
    stats_df  = pd.read_csv(STATS_FILE,  low_memory=False)
    salary_df = pd.read_csv(SALARY_FILE, low_memory=False)
    print(f"player stats: {len(stats_df):,} rows  |  salary: {len(salary_df):,} rows")

    # Summarise each dataset to one record per player
    stats_summary  = summarise_players(stats_df)
    salary_summary = summarise_players(salary_df)
    print(f"Unique players — stats: {len(stats_summary)}  |  salary: {len(salary_summary)}")

    # Build the unified dimension table
    dim_df = build_dim_players(stats_summary, salary_summary)

    # Breakdown: how many players came from each source
    stats_names  = set(stats_summary.keys())
    abbrev_map   = build_salary_abbrev_map(salary_summary, stats_summary)
    matched_sal  = set(abbrev_map.keys())          # abbrev names that matched salary
    salary_only  = len(salary_summary) - len(abbrev_map)

    print(f"\nPlayer sources:")
    print(f"  player_stats only (no contract record) : {len(stats_names) - len(matched_sal)}")
    print(f"  Matched across both datasets           : {len(matched_sal)}")
    print(f"  salary only (no offensive PBP stats)   : {salary_only}")

    # Save
    os.makedirs(CLEAN_DIR, exist_ok=True)
    dim_df.to_csv(OUTPUT_FILE, index=False)

    print(f"\nFinal row count : {len(dim_df)}")
    print(f"Saved           : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
