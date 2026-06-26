"""
Phase 3 - Import clean CSVs into bearlytics.db
Run from any directory:  python 03_sql/02_import.py
"""

import sqlite3
import os
import sys

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR  = os.path.dirname(SCRIPT_DIR)
CLEAN_DIR    = os.path.join(PROJECT_DIR, "02_clean_data")
DB_PATH      = os.path.join(SCRIPT_DIR, "bearlytics.db")
SCHEMA_PATH  = os.path.join(SCRIPT_DIR, "01_schema.sql")

# CSV path (relative to CLEAN_DIR) -> target table name
CSV_TABLE_MAP = [
    (os.path.join("dimension_tables", "dim_teams.csv"),        "dim_teams"),
    (os.path.join("dimension_tables", "dim_players.csv"),      "dim_players"),
    (os.path.join("dimension_tables", "dim_positions.csv"),    "dim_positions"),
    (os.path.join("dimension_tables", "date_dimension.csv"),   "date_dimension"),
    (os.path.join("fact_tables", "bears_team_stats_2016_2025.csv"),   "fact_team_stats"),
    (os.path.join("fact_tables", "bears_game_logs_2016_2025.csv"),    "fact_game_logs"),
    (os.path.join("fact_tables", "bears_player_stats_2016_2025.csv"), "fact_player_stats"),
    (os.path.join("fact_tables", "bears_salary_data_2016_2025.csv"),  "fact_salary_data"),
    (os.path.join("fact_tables", "nfl_league_stats_2016_2025.csv"),   "fact_nfl_league_stats"),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def apply_schema(conn: sqlite3.Connection, schema_path: str) -> None:
    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()
    conn.executescript(sql)
    conn.commit()


def import_csv(conn: sqlite3.Connection, csv_path: str, table: str) -> int:
    df = pd.read_csv(csv_path)
    df.to_sql(table, conn, if_exists="append", index=False)
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("Bearlytics Phase 3 — Database Import")
    print("=" * 60)

    # Verify source directory exists
    if not os.path.isdir(CLEAN_DIR):
        print(f"ERROR: Clean data directory not found:\n  {CLEAN_DIR}")
        sys.exit(1)

    # Remove stale DB so import is always idempotent
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed existing DB: {DB_PATH}")

    conn = connect(DB_PATH)

    # Apply schema DDL
    apply_schema(conn, SCHEMA_PATH)
    print("Schema applied.\n")

    # Import each CSV
    errors = 0
    print(f"{'Table':<30} {'Rows':>8}")
    print("-" * 40)
    for csv_rel, table in CSV_TABLE_MAP:
        csv_path = os.path.join(CLEAN_DIR, csv_rel)
        if not os.path.isfile(csv_path):
            print(f"  MISSING: {csv_path}")
            errors += 1
            continue
        try:
            count = import_csv(conn, csv_path, table)
            print(f"  {table:<28} {count:>8,}")
        except Exception as exc:
            print(f"  ERROR loading {table}: {exc}")
            errors += 1

    conn.close()

    print("-" * 40)
    if errors == 0:
        print(f"\nDatabase ready: {DB_PATH}")
    else:
        print(f"\n{errors} error(s) encountered. Check messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
