#!/usr/bin/env python3
"""
build_bears_salary_data.py

Downloads and processes real Chicago Bears player contract data for
seasons 2016–2025 using the nflverse historical contracts dataset
(originally sourced from OverTheCap.com, maintained by nflverse).

Data source:
  https://github.com/nflverse/nflverse-data/releases/download/contracts/historical_contracts.csv.gz
  Published April 2022. Contains contracts signed through approximately April 2022.

What this dataset contains (contract-level — one record per contract signed):
  Player_Name, Position, Team, Season (derived), Contract_Value,
  Contract_Length_Years, Guaranteed_Money

Known data gap:
  The nflverse contracts file was published in April 2022 and has not been
  updated since. Contracts signed after April 2022 are absent. Seasons 2023–2025
  will only reflect multi-year deals signed in 2022 or earlier that extend into
  those years; newly signed contracts from 2023 onward are missing entirely.

What is NOT available from this source (columns left blank):
  Age            — date of birth is not in the contracts file
  Cap_Hit        — requires per-year cap table pages from OverTheCap;
                   those historical pages (e.g. /salary-cap/chicago-bears/2022)
                   all return HTTP 404 — they are not publicly accessible
  Base_Salary    — same reason as Cap_Hit
  Signing_Bonus  — same reason as Cap_Hit
  Roster_Bonus   — same reason as Cap_Hit
  Dead_Cap       — same reason as Cap_Hit

How team codes work in this file:
  Single-team contracts  →  full team name, e.g. "Bears"
  Multi-team contracts   →  slash-separated abbreviations, e.g. "CHI/ATL"
                            (teams listed in order the player played under
                            that contract; "CHI/ATL" = started in CHI, then ATL)
  This script includes both "Bears" rows and any row where "CHI" appears
  as a slash-delimited token.

How Season is derived:
  The contracts file records year_signed (when the contract was executed)
  and years (contract length in seasons). This script expands each Bears
  contract into one row per season it is active, intersected with 2016–2025.
  Example: a 4-year deal signed in 2019 creates rows for 2019, 2020, 2021, 2022.

  Contract_Value and Guaranteed_Money repeat in every season row because
  they describe the full contract, not a single-year amount.

Output:
  01_raw_data/salary_data/bears_salary_{year}.csv   — one file per season
  03_clean_data/bears_salary_data_2016_2025.csv      — combined master file

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

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TEAM        = "CHI"
SEASONS     = set(range(2016, 2026))   # 2016 through 2025 inclusive

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
SALARY_DIR  = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "01_raw_data", "salary_data"))
CLEAN_DIR   = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "03_clean_data"))
CACHE_DIR   = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "01_raw_data", "_cache"))

CONTRACTS_URL = (
    "https://github.com/nflverse/nflverse-data/releases/download/"
    "contracts/historical_contracts.csv.gz"
)

# Final column order — matches the user spec exactly
OUTPUT_COLS = [
    "Season",
    "Player_Name",
    "Position",
    "Team",
    "Age",               # blank — DOB not in source
    "Cap_Hit",           # blank — per-season pages not accessible (see module docstring)
    "Base_Salary",       # blank — same reason
    "Signing_Bonus",     # blank — same reason
    "Roster_Bonus",      # blank — same reason
    "Dead_Cap",          # blank — same reason
    "Guaranteed_Money",  # total guaranteed across full contract
    "Contract_Value",    # total contract value across all years
    "Contract_Length_Years",
]


# ---------------------------------------------------------------------------
# Download helper
# ---------------------------------------------------------------------------

def fetch_contracts() -> pd.DataFrame:
    """
    Load the nflverse historical contracts file.
    Downloads once and caches locally; subsequent runs read from cache.
    """
    cache_path = os.path.join(CACHE_DIR, "historical_contracts.csv.gz")

    if not os.path.exists(cache_path):
        print("Downloading historical_contracts.csv.gz ...", end=" ", flush=True)
        try:
            resp = requests.get(CONTRACTS_URL, stream=True, timeout=60)
            resp.raise_for_status()
        except requests.RequestException as exc:
            sys.exit(f"\nDownload failed: {exc}")

        total     = int(resp.headers.get("content-length", 0))
        received  = 0

        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(cache_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=65536):
                f.write(chunk)
                received += len(chunk)
                if total > 0:
                    print(
                        f"\r  Downloading historical_contracts.csv.gz ... "
                        f"{received / 1e6:.1f}/{total / 1e6:.1f} MB",
                        end="", flush=True,
                    )
        print(" done.")
    else:
        print("Using cached historical_contracts.csv.gz")

    return pd.read_csv(cache_path, low_memory=False)


# ---------------------------------------------------------------------------
# Processing helpers
# ---------------------------------------------------------------------------

def is_bears_contract(team_str: str) -> bool:
    """
    Return True if this contract involves the Bears.

    The contracts file uses two formats:
      - Full name for single-team deals:  "Bears"
      - Slash-separated abbreviations for multi-team deals: "CHI/ATL", "DEN/CHI"

    We match "Bears" exactly, or "CHI" as a standalone token in the slash list.
    Plain "CHI" does not appear as a standalone value in this dataset — the Bears
    are always represented as either "Bears" or "CHI" within a slash-delimited
    multi-team string.
    """
    if pd.isna(team_str):
        return False
    team_str = str(team_str)
    return team_str == "Bears" or "CHI" in team_str.split("/")


def filter_bears_contracts(contracts: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only Bears contracts that overlap with the 2016–2025 window.

    Filtering logic:
      is_bears_contract(team)            →  Bears were involved in the contract
      year_signed > 0                    →  drop records with missing/invalid year
      year_signed <= 2025                →  contract starts before our window closes
      year_signed + years - 1 >= 2016   →  contract is still active within our window
    """
    bears = contracts[contracts["team"].apply(is_bears_contract)].copy()

    # Drop records with missing or zero year / length (cannot determine season coverage)
    bears = bears.dropna(subset=["year_signed", "years"])
    bears["year_signed"] = bears["year_signed"].astype(int)
    bears["years"]       = bears["years"].astype(int)

    # year_signed == 0 means the signing year was not recorded in OTC — skip these
    bears = bears[bears["year_signed"] > 0]

    # Keep only contracts that overlap 2016–2025
    bears = bears[
        (bears["year_signed"] <= 2025) &
        (bears["year_signed"] + bears["years"] - 1 >= 2016)
    ]
    return bears.reset_index(drop=True)


def expand_to_seasons(bears: pd.DataFrame) -> pd.DataFrame:
    """
    Explode each contract into one row per active season within 2016–2025.

    Contract_Value and Guaranteed_Money are contract totals repeated in
    every season row. They do NOT represent the cap hit for that year.
    """
    rows = []

    for _, contract in bears.iterrows():
        year_signed = int(contract["year_signed"])
        years       = int(contract["years"])

        # Seasons this contract covers, clipped to our target window
        active_seasons = sorted(
            set(range(year_signed, year_signed + years)) & SEASONS
        )

        for season in active_seasons:
            rows.append({
                "Season":               season,
                "Player_Name":          contract["player"],
                "Position":             contract["position"],
                "Team":                 TEAM,
                "Age":                  "",   # not in source — see module docstring
                "Cap_Hit":              "",   # not in source — see module docstring
                "Base_Salary":          "",   # not in source — see module docstring
                "Signing_Bonus":        "",   # not in source — see module docstring
                "Roster_Bonus":         "",   # not in source — see module docstring
                "Dead_Cap":             "",   # not in source — see module docstring
                "Guaranteed_Money":     contract["guaranteed"],
                "Contract_Value":       contract["value"],
                "Contract_Length_Years": years,
            })

    return pd.DataFrame(rows, columns=OUTPUT_COLS)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    os.makedirs(SALARY_DIR, exist_ok=True)
    os.makedirs(CLEAN_DIR,  exist_ok=True)
    os.makedirs(CACHE_DIR,  exist_ok=True)

    # --- Load contracts ---
    contracts = fetch_contracts()
    print(f"Total contracts in file: {len(contracts):,}")

    # Show team codes present so users can spot any naming issue
    team_codes = sorted(contracts["team"].dropna().unique())
    print(f"Sample team codes: {team_codes[:8]} ...")

    # --- Filter and expand ---
    bears = filter_bears_contracts(contracts)
    print(f"Bears contracts overlapping 2016–2025: {len(bears)}")

    if bears.empty:
        sys.exit('No Bears contracts found — expected "Bears" or "CHI" in team field.')

    expanded = expand_to_seasons(bears)
    print(f"Expanded to {len(expanded):,} player-season rows\n")

    # --- Save per-season files ---
    all_seasons = []

    for season in sorted(SEASONS):
        season_df = (
            expanded[expanded["Season"] == season]
            .sort_values("Player_Name")
            .reset_index(drop=True)
        )

        if season_df.empty:
            print(f"  {season}: no contracts found")
            continue

        out_path = os.path.join(SALARY_DIR, f"bears_salary_{season}.csv")
        season_df.to_csv(out_path, index=False)
        print(f"  {season}: {len(season_df):>3} contracts  ->  {os.path.basename(out_path)}")
        all_seasons.append(season_df)

    if not all_seasons:
        print("No season files written.")
        return

    # --- Save master file ---
    master = pd.concat(all_seasons, ignore_index=True)
    master_path = os.path.join(CLEAN_DIR, "bears_salary_data_2016_2025.csv")
    master.to_csv(master_path, index=False)

    print(f"\nMaster file  ->  {master_path}")
    print(f"Total rows   :  {len(master):,}")
    print(f"Unique players: {master['Player_Name'].nunique()}")
    print()
    print("NOTE: Cap_Hit, Base_Salary, Signing_Bonus, Roster_Bonus, Dead_Cap, and Age")
    print("are blank because per-season cap breakdown data is not publicly accessible")
    print("from any free, scrapeable source. See module docstring for full explanation.")


if __name__ == "__main__":
    main()
