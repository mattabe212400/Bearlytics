#!/usr/bin/env python3
"""
create_dim_positions.py

Builds a position lookup/dimension table from the unique Position values
found in dim_players.csv.

Output columns:
  Position_ID    — auto-incrementing integer (1-based, sorted alphabetically)
  Position       — position abbreviation  (e.g. QB, WR, DE)
  Position_Group — Offense | Defense | Special Teams | Unknown

Input:
  03_clean_data/dim_players.csv

Output:
  03_clean_data/dim_positions.csv
"""

import os
import sys

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
CLEAN_DIR    = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "03_clean_data"))

INPUT_FILE   = os.path.join(CLEAN_DIR, "dim_players.csv")
OUTPUT_FILE  = os.path.join(CLEAN_DIR, "dim_positions.csv")

# ---------------------------------------------------------------------------
# Position → Position_Group mapping
# ---------------------------------------------------------------------------

POSITION_GROUP: dict[str, str] = {
    # Offense — skill positions
    "QB":   "Offense",
    "RB":   "Offense",
    "FB":   "Offense",
    "WR":   "Offense",
    "TE":   "Offense",
    # Offense — offensive line
    "C":    "Offense",
    "LG":   "Offense",
    "RG":   "Offense",
    "LT":   "Offense",
    "RT":   "Offense",
    "OL":   "Offense",
    "OT":   "Offense",
    "OG":   "Offense",
    # Defense — defensive line
    "DL":   "Defense",
    "DE":   "Defense",
    "DT":   "Defense",
    "IDL":  "Defense",
    "NT":   "Defense",
    "EDGE": "Defense",
    "ED":   "Defense",
    # Defense — linebackers
    "LB":   "Defense",
    "ILB":  "Defense",
    "OLB":  "Defense",
    # Defense — secondary
    "CB":   "Defense",
    "S":    "Defense",
    "FS":   "Defense",
    "SS":   "Defense",
    "DB":   "Defense",
    # Special Teams
    "K":    "Special Teams",
    "P":    "Special Teams",
    "LS":   "Special Teams",
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not os.path.exists(INPUT_FILE):
        sys.exit(f"File not found: {INPUT_FILE}\nRun create_dim_players.py first.")

    # Load the player dimension table
    players_df = pd.read_csv(INPUT_FILE, low_memory=False)

    # Collect unique, non-blank position values
    positions = (
        players_df["Position"]
        .dropna()
        .astype(str)
        .str.strip()
        .replace("", pd.NA)
        .dropna()
        .unique()
        .tolist()
    )

    # Sort alphabetically (case-insensitive)
    positions = sorted(positions, key=str.upper)

    # Build one row per position, mapping to its group
    rows = []
    unmapped = []
    for pos in positions:
        group = POSITION_GROUP.get(pos, "Unknown")
        if group == "Unknown":
            unmapped.append(pos)
        rows.append({"Position": pos, "Position_Group": group})

    # Assemble DataFrame and add Position_ID (1-based after alphabetical sort)
    dim_df = pd.DataFrame(rows)
    dim_df.insert(0, "Position_ID", range(1, len(dim_df) + 1))

    # Warn about any positions not covered by the mapping
    if unmapped:
        print(f"  Note: {len(unmapped)} position(s) not in mapping → grouped as 'Unknown': {unmapped}")

    # Save
    os.makedirs(CLEAN_DIR, exist_ok=True)
    dim_df.to_csv(OUTPUT_FILE, index=False)

    print(f"Final row count : {len(dim_df)}")
    print(f"Saved           : {OUTPUT_FILE}")

    # Print the full table for a quick visual check
    print()
    print(dim_df.to_string(index=False))


if __name__ == "__main__":
    main()
