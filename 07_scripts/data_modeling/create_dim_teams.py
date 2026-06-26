#!/usr/bin/env python3
"""
create_dim_teams.py

Builds a team dimension table for Power BI using every team abbreviation
found in nfl_league_stats_2016_2025.csv, enriched with a static lookup
for Conference, Division, City, and Nickname.

Output columns:
  Team_ID     — auto-incrementing integer (1-based, sorted by Team abbreviation)
  Team        — 2-3 letter abbreviation matching the fact tables (e.g. CHI, GB)
  Team_Name   — full franchise name (e.g. Chicago Bears)
  Conference  — AFC or NFC
  Division    — e.g. NFC North
  City        — primary city or metro area
  Nickname    — team nickname without city (e.g. Bears)

Input:
  03_clean_data/nfl_league_stats_2016_2025.csv

Output:
  03_clean_data/dim_teams.csv
"""

import os
import sys

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
CLEAN_DIR    = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "03_clean_data"))

INPUT_FILE   = os.path.join(CLEAN_DIR, "nfl_league_stats_2016_2025.csv")
OUTPUT_FILE  = os.path.join(CLEAN_DIR, "dim_teams.csv")

# ---------------------------------------------------------------------------
# Static lookup — all 32 current NFL franchises
# Abbreviations match nflverse conventions used throughout the project.
# Relocated teams use their current abbreviation (LV not OAK, LAC not SD).
# ---------------------------------------------------------------------------

TEAM_LOOKUP: dict[str, dict] = {
    # ── AFC East ──────────────────────────────────────────────────────────
    "BUF": {"Team_Name": "Buffalo Bills",            "Conference": "AFC", "Division": "AFC East",  "City": "Buffalo",        "Nickname": "Bills"},
    "MIA": {"Team_Name": "Miami Dolphins",           "Conference": "AFC", "Division": "AFC East",  "City": "Miami",          "Nickname": "Dolphins"},
    "NE":  {"Team_Name": "New England Patriots",     "Conference": "AFC", "Division": "AFC East",  "City": "New England",    "Nickname": "Patriots"},
    "NYJ": {"Team_Name": "New York Jets",            "Conference": "AFC", "Division": "AFC East",  "City": "New York",       "Nickname": "Jets"},
    # ── AFC North ─────────────────────────────────────────────────────────
    "BAL": {"Team_Name": "Baltimore Ravens",         "Conference": "AFC", "Division": "AFC North", "City": "Baltimore",      "Nickname": "Ravens"},
    "CIN": {"Team_Name": "Cincinnati Bengals",       "Conference": "AFC", "Division": "AFC North", "City": "Cincinnati",     "Nickname": "Bengals"},
    "CLE": {"Team_Name": "Cleveland Browns",         "Conference": "AFC", "Division": "AFC North", "City": "Cleveland",      "Nickname": "Browns"},
    "PIT": {"Team_Name": "Pittsburgh Steelers",      "Conference": "AFC", "Division": "AFC North", "City": "Pittsburgh",     "Nickname": "Steelers"},
    # ── AFC South ─────────────────────────────────────────────────────────
    "HOU": {"Team_Name": "Houston Texans",           "Conference": "AFC", "Division": "AFC South", "City": "Houston",        "Nickname": "Texans"},
    "IND": {"Team_Name": "Indianapolis Colts",       "Conference": "AFC", "Division": "AFC South", "City": "Indianapolis",   "Nickname": "Colts"},
    "JAX": {"Team_Name": "Jacksonville Jaguars",     "Conference": "AFC", "Division": "AFC South", "City": "Jacksonville",   "Nickname": "Jaguars"},
    "TEN": {"Team_Name": "Tennessee Titans",         "Conference": "AFC", "Division": "AFC South", "City": "Nashville",      "Nickname": "Titans"},
    # ── AFC West ──────────────────────────────────────────────────────────
    "DEN": {"Team_Name": "Denver Broncos",           "Conference": "AFC", "Division": "AFC West",  "City": "Denver",         "Nickname": "Broncos"},
    "KC":  {"Team_Name": "Kansas City Chiefs",       "Conference": "AFC", "Division": "AFC West",  "City": "Kansas City",    "Nickname": "Chiefs"},
    "LAC": {"Team_Name": "Los Angeles Chargers",     "Conference": "AFC", "Division": "AFC West",  "City": "Los Angeles",    "Nickname": "Chargers"},
    "LV":  {"Team_Name": "Las Vegas Raiders",        "Conference": "AFC", "Division": "AFC West",  "City": "Las Vegas",      "Nickname": "Raiders"},
    # ── NFC East ──────────────────────────────────────────────────────────
    "DAL": {"Team_Name": "Dallas Cowboys",           "Conference": "NFC", "Division": "NFC East",  "City": "Dallas",         "Nickname": "Cowboys"},
    "NYG": {"Team_Name": "New York Giants",          "Conference": "NFC", "Division": "NFC East",  "City": "New York",       "Nickname": "Giants"},
    "PHI": {"Team_Name": "Philadelphia Eagles",      "Conference": "NFC", "Division": "NFC East",  "City": "Philadelphia",   "Nickname": "Eagles"},
    "WAS": {"Team_Name": "Washington Commanders",    "Conference": "NFC", "Division": "NFC East",  "City": "Washington",     "Nickname": "Commanders"},
    # ── NFC North ─────────────────────────────────────────────────────────
    "CHI": {"Team_Name": "Chicago Bears",            "Conference": "NFC", "Division": "NFC North", "City": "Chicago",        "Nickname": "Bears"},
    "DET": {"Team_Name": "Detroit Lions",            "Conference": "NFC", "Division": "NFC North", "City": "Detroit",        "Nickname": "Lions"},
    "GB":  {"Team_Name": "Green Bay Packers",        "Conference": "NFC", "Division": "NFC North", "City": "Green Bay",      "Nickname": "Packers"},
    "MIN": {"Team_Name": "Minnesota Vikings",        "Conference": "NFC", "Division": "NFC North", "City": "Minneapolis",    "Nickname": "Vikings"},
    # ── NFC South ─────────────────────────────────────────────────────────
    "ATL": {"Team_Name": "Atlanta Falcons",          "Conference": "NFC", "Division": "NFC South", "City": "Atlanta",        "Nickname": "Falcons"},
    "CAR": {"Team_Name": "Carolina Panthers",        "Conference": "NFC", "Division": "NFC South", "City": "Charlotte",      "Nickname": "Panthers"},
    "NO":  {"Team_Name": "New Orleans Saints",       "Conference": "NFC", "Division": "NFC South", "City": "New Orleans",    "Nickname": "Saints"},
    "TB":  {"Team_Name": "Tampa Bay Buccaneers",     "Conference": "NFC", "Division": "NFC South", "City": "Tampa Bay",      "Nickname": "Buccaneers"},
    # ── NFC West ──────────────────────────────────────────────────────────
    "ARI": {"Team_Name": "Arizona Cardinals",        "Conference": "NFC", "Division": "NFC West",  "City": "Phoenix",        "Nickname": "Cardinals"},
    "LA":  {"Team_Name": "Los Angeles Rams",         "Conference": "NFC", "Division": "NFC West",  "City": "Los Angeles",    "Nickname": "Rams"},
    "SF":  {"Team_Name": "San Francisco 49ers",      "Conference": "NFC", "Division": "NFC West",  "City": "San Francisco",  "Nickname": "49ers"},
    "SEA": {"Team_Name": "Seattle Seahawks",         "Conference": "NFC", "Division": "NFC West",  "City": "Seattle",        "Nickname": "Seahawks"},
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not os.path.exists(INPUT_FILE):
        sys.exit(f"File not found: {INPUT_FILE}")

    # Load the league stats dataset and extract unique team abbreviations
    league_df   = pd.read_csv(INPUT_FILE, low_memory=False)
    teams_found = sorted(league_df["Team"].dropna().unique().tolist())
    print(f"Unique team abbreviations in dataset: {len(teams_found)}")

    rows    = []
    unknown = []

    for team in teams_found:
        info = TEAM_LOOKUP.get(team)
        if info:
            rows.append({"Team": team, **info})
        else:
            # Team code not in static lookup — include with placeholder values
            unknown.append(team)
            rows.append({
                "Team":       team,
                "Team_Name":  "Unknown",
                "Conference": "Unknown",
                "Division":   "Unknown",
                "City":       "Unknown",
                "Nickname":   "Unknown",
            })

    if unknown:
        print(f"  Note: {len(unknown)} team(s) not in static lookup → 'Unknown': {unknown}")

    # Sort alphabetically by Team abbreviation, then assign Team_ID
    dim_df = (
        pd.DataFrame(rows)
        .sort_values("Team")
        .reset_index(drop=True)
    )
    dim_df.insert(0, "Team_ID", range(1, len(dim_df) + 1))

    # Enforce final column order
    dim_df = dim_df[["Team_ID", "Team", "Team_Name", "Conference", "Division", "City", "Nickname"]]

    # Save
    os.makedirs(CLEAN_DIR, exist_ok=True)
    dim_df.to_csv(OUTPUT_FILE, index=False)

    print(f"Final row count : {len(dim_df)}")
    print(f"Saved           : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
