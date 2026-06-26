#!/usr/bin/env python3
"""
download_nfl_team_logos.py

Downloads official NFL team logos (500 px PNG) for all 32 active teams
using URLs from the nflverse teams_colors_logos dataset (pointing to
ESPN's CDN).  Also downloads bears_logo.png and nfl_logo.png.

Source:
  Team logo URLs  →  nflverse teams_colors_logos.csv
  NFL league logo →  nflverse team_league_logo column (same file)

Output:
  01_raw_data/logos/{ABBR}.png      — one file per team (e.g. CHI.png)
  01_raw_data/logos/bears_logo.png  — duplicate of CHI.png
  01_raw_data/logos/nfl_logo.png    — NFL shield logo

Skips download if file already exists (safe to re-run).

Historical franchises in the nflverse file (OAK, SD, STL) are skipped
because they are relocated teams now covered by LV, LAC, and LA/LAR.

Setup:
  pip install requests pandas
"""

import os
import sys
import time

import pandas as pd

try:
    import requests
except ImportError:
    sys.exit("requests is not installed. Run: pip install requests pandas")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGOS_DIR  = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "01_raw_data", "logos"))

TEAMS_CSV_URL = (
    "https://github.com/nflverse/nflverse-data/releases/download/"
    "teams/teams_colors_logos.csv"
)

# Relocated franchises kept in the nflverse file for historical reference.
# Their logos are now served under the current team's abbreviation (LV, LAC,
# LA/LAR), so downloading under the old name would create redundant/confusing
# files.
SKIP_ABBREVS = {"OAK", "SD", "STL"}


# ---------------------------------------------------------------------------
# Download helper
# ---------------------------------------------------------------------------

def download_logo(url: str, dest_path: str, label: str) -> bool:
    """
    Download a PNG from url and save to dest_path.
    Skips the download if the file already exists.
    Returns True on success or skip, False on failure.
    """
    if os.path.exists(dest_path):
        print(f"  skip (exists)  {label}")
        return True

    try:
        resp = requests.get(url, timeout=30, stream=True)
        resp.raise_for_status()

        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        # Basic sanity check — PNG files start with the 8-byte PNG signature
        with open(dest_path, "rb") as f:
            header = f.read(8)
        if header[:4] != b"\x89PNG":
            os.remove(dest_path)
            raise ValueError("Downloaded file is not a valid PNG")

        print(f"  ok             {label}")
        return True

    except Exception as exc:
        # Remove partial file if something went wrong mid-download
        if os.path.exists(dest_path):
            os.remove(dest_path)
        print(f"  FAIL           {label}  —  {exc}")
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    os.makedirs(LOGOS_DIR, exist_ok=True)

    # --- Load the nflverse teams data for logo URLs ---
    print("Loading team data from nflverse ...", end=" ", flush=True)
    try:
        teams = pd.read_csv(TEAMS_CSV_URL, low_memory=False)
    except Exception as exc:
        sys.exit(f"\nFailed to load teams data: {exc}")
    print(f"{len(teams)} rows\n")

    # --- Download one logo per team abbreviation ---
    ok   = 0
    fail = 0

    for _, row in teams.iterrows():
        abbr     = str(row["team_abbr"]).strip()
        logo_url = str(row["team_logo_espn"]).strip()
        name     = str(row["team_name"]).strip()

        # Skip relocated/historical franchises
        if abbr in SKIP_ABBREVS:
            print(f"  skip (historical) {abbr} ({name})")
            continue

        if not logo_url.startswith("http"):
            print(f"  skip (no URL)  {abbr}")
            continue

        dest = os.path.join(LOGOS_DIR, f"{abbr}.png")
        result = download_logo(logo_url, dest, f"{abbr}.png  ({name})")

        if result:
            ok += 1
        else:
            fail += 1

        # Small delay between requests to avoid hammering ESPN's CDN
        time.sleep(0.15)

    # --- bears_logo.png — a dedicated Bears logo for the Bearlytics project ---
    print()
    chi_row = teams[teams["team_abbr"] == "CHI"]
    if not chi_row.empty:
        bears_url  = str(chi_row.iloc[0]["team_logo_espn"]).strip()
        bears_dest = os.path.join(LOGOS_DIR, "bears_logo.png")
        if download_logo(bears_url, bears_dest, "bears_logo.png  (Chicago Bears — project logo)"):
            ok += 1
        else:
            fail += 1
        time.sleep(0.15)

    # --- nfl_logo.png — the NFL shield from the nflverse league logo column ---
    # team_league_logo is the same URL for every row; grab the first non-null value.
    nfl_logo_url = teams["team_league_logo"].dropna().iloc[0]
    nfl_dest     = os.path.join(LOGOS_DIR, "nfl_logo.png")
    if download_logo(str(nfl_logo_url).strip(), nfl_dest, "nfl_logo.png  (NFL league logo)"):
        ok += 1
    else:
        fail += 1

    # --- Summary ---
    print()
    saved = len([f for f in os.listdir(LOGOS_DIR) if f.endswith(".png")])
    print(f"Results : {ok} succeeded, {fail} failed")
    print(f"PNG files in logos folder: {saved}")
    print(f"Location: {LOGOS_DIR}")


if __name__ == "__main__":
    main()
