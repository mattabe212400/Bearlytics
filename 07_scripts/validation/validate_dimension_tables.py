#!/usr/bin/env python3
"""
validate_dimension_tables.py

Phase 2 — dimension table quality audit.

Validates the four dimension tables in 03_clean_data/:
  date_dimension.csv
  dim_players.csv
  dim_positions.csv
  dim_teams.csv

Checks performed:
  1.  Row count
  2.  Column count
  3.  Duplicate primary keys
  4.  Missing / blank values
  5.  dim_positions  — Position_Group values are valid
  6.  dim_teams      — exactly 32 NFL teams present
  7.  dim_teams      — every team in nfl_league_stats_2016_2025.csv is covered
  8.  dim_positions  — every position in bears_player_stats_2016_2025.csv is covered
  9.  Validation summary

DOES NOT modify any dataset — reporting only.

Outputs:
  Terminal:  per-table findings + summary
  07_documentation/dimension_validation_report.md
"""

import os
import sys
from datetime import datetime

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
CLEAN_DIR    = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "03_clean_data"))
DOCS_DIR     = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "07_documentation"))

REPORT_FILE  = os.path.join(DOCS_DIR, "dimension_validation_report.md")

# Dimension tables to validate (filename → primary key column)
DIMENSIONS: dict[str, str] = {
    "date_dimension.csv": "Date",
    "dim_players.csv":    "Player_ID",
    "dim_positions.csv":  "Position_ID",
    "dim_teams.csv":      "Team_ID",
}

# Reference fact tables used in cross-table checks
LEAGUE_STATS_FILE  = os.path.join(CLEAN_DIR, "nfl_league_stats_2016_2025.csv")
PLAYER_STATS_FILE  = os.path.join(CLEAN_DIR, "bears_player_stats_2016_2025.csv")

# Valid values for dim_positions.Position_Group
VALID_POSITION_GROUPS = {"Offense", "Defense", "Special Teams", "Unknown"}

EXPECTED_TEAM_COUNT = 32

# ---------------------------------------------------------------------------
# Finding type  (same pattern as validate_datasets.py)
# ---------------------------------------------------------------------------

STATUS_ICON = {"ERROR": "❌", "WARNING": "⚠️ ", "OK": "✅", "INFO": "ℹ️ "}
STATUS_TAG  = {"ERROR": "[ERROR]", "WARNING": "[WARN] ", "OK": "[OK]   ", "INFO": "[INFO] "}


class Finding:
    __slots__ = ("check", "status", "detail")

    def __init__(self, check: str, status: str, detail: str) -> None:
        self.check  = check
        self.status = status
        self.detail = detail


# ---------------------------------------------------------------------------
# Generic checks (applied to every dimension table)
# ---------------------------------------------------------------------------

def chk_shape(df: pd.DataFrame) -> list:
    return [Finding("Shape", "INFO", f"{len(df):,} rows × {len(df.columns)} columns")]


def chk_duplicate_pks(df: pd.DataFrame, pk_col: str) -> list:
    if pk_col not in df.columns:
        return [Finding("Duplicate PKs", "WARNING", f"Primary key column '{pk_col}' not found")]
    n = int(df.duplicated(subset=[pk_col]).sum())
    if n:
        return [Finding("Duplicate PKs", "ERROR", f"{n} duplicate values in '{pk_col}'")]
    return [Finding("Duplicate PKs", "OK", f"No duplicates in '{pk_col}'")]


def chk_missing_values(df: pd.DataFrame) -> list:
    findings = []
    has_missing = False
    for col in df.columns:
        null_count  = int(df[col].isnull().sum())
        blank_count = 0
        if df[col].dtype == object:
            non_null    = df[col].dropna()
            blank_count = int((non_null.astype(str).str.strip() == "").sum())
        total = null_count + blank_count
        if total:
            has_missing = True
            pct = total / len(df) * 100
            findings.append(Finding(
                f"Missing: {col}",
                "WARNING",
                f"{total:,}/{len(df):,} ({pct:.1f}%) missing or blank",
            ))
    if not has_missing:
        findings.append(Finding("Missing values", "OK", "No missing or blank values"))
    return findings


# ---------------------------------------------------------------------------
# Dimension-specific checks
# ---------------------------------------------------------------------------

def chk_position_groups(df: pd.DataFrame) -> list:
    """dim_positions — all Position_Group values must be in the allowed set."""
    if "Position_Group" not in df.columns:
        return [Finding("Position_Group values", "WARNING", "Column 'Position_Group' not found")]

    actual   = set(df["Position_Group"].dropna().astype(str).str.strip().unique())
    invalid  = actual - VALID_POSITION_GROUPS
    unknowns = actual & {"Unknown"}

    findings = []
    if invalid:
        findings.append(Finding(
            "Position_Group values",
            "ERROR",
            f"Unrecognised groups: {sorted(invalid)}",
        ))
    if unknowns:
        findings.append(Finding(
            "Position_Group: Unknown",
            "WARNING",
            f"Some positions mapped to 'Unknown' — consider adding them to the mapping",
        ))
    if not findings:
        findings.append(Finding(
            "Position_Group values",
            "OK",
            f"All values are valid: {sorted(actual)}",
        ))
    return findings


def chk_team_count(df: pd.DataFrame) -> list:
    """dim_teams — exactly 32 NFL teams expected."""
    if "Team" not in df.columns:
        return [Finding("Team count", "WARNING", "Column 'Team' not found")]
    n = df["Team"].nunique()
    if n != EXPECTED_TEAM_COUNT:
        return [Finding(
            "Team count",
            "WARNING",
            f"{n} unique teams found (expected {EXPECTED_TEAM_COUNT})",
        )]
    return [Finding("Team count", "OK", f"Exactly {EXPECTED_TEAM_COUNT} teams present")]


def chk_teams_coverage(dim_teams_df: pd.DataFrame) -> list:
    """
    Cross-table check: every Team abbreviation in nfl_league_stats_2016_2025.csv
    must exist in dim_teams.
    """
    if not os.path.exists(LEAGUE_STATS_FILE):
        return [Finding(
            "League stats coverage",
            "WARNING",
            f"Reference file not found: {os.path.basename(LEAGUE_STATS_FILE)}",
        )]
    if "Team" not in dim_teams_df.columns:
        return [Finding("League stats coverage", "WARNING", "Column 'Team' not found in dim_teams")]

    league_df    = pd.read_csv(LEAGUE_STATS_FILE, low_memory=False)
    stats_teams  = set(league_df["Team"].dropna().astype(str).str.strip().unique())
    dim_teams    = set(dim_teams_df["Team"].dropna().astype(str).str.strip().unique())
    missing      = stats_teams - dim_teams

    if missing:
        return [Finding(
            "League stats coverage",
            "ERROR",
            f"{len(missing)} team(s) in league stats not in dim_teams: {sorted(missing)}",
        )]
    return [Finding(
        "League stats coverage",
        "OK",
        f"All {len(stats_teams)} teams from nfl_league_stats are covered by dim_teams",
    )]


def chk_positions_coverage(dim_positions_df: pd.DataFrame) -> list:
    """
    Cross-table check: every non-blank Position in bears_player_stats_2016_2025.csv
    must exist in dim_positions.
    """
    if not os.path.exists(PLAYER_STATS_FILE):
        return [Finding(
            "Player stats coverage",
            "WARNING",
            f"Reference file not found: {os.path.basename(PLAYER_STATS_FILE)}",
        )]
    if "Position" not in dim_positions_df.columns:
        return [Finding("Player stats coverage", "WARNING", "Column 'Position' not found in dim_positions")]

    stats_df = pd.read_csv(PLAYER_STATS_FILE, low_memory=False)
    # Only consider non-blank positions
    stats_pos = set(
        stats_df["Position"]
        .dropna()
        .astype(str)
        .str.strip()
        .replace("", pd.NA)
        .dropna()
        .unique()
    )
    dim_pos = set(dim_positions_df["Position"].dropna().astype(str).str.strip().unique())
    missing = stats_pos - dim_pos

    if missing:
        return [Finding(
            "Player stats coverage",
            "ERROR",
            f"{len(missing)} position(s) in player stats not in dim_positions: {sorted(missing)}",
        )]
    return [Finding(
        "Player stats coverage",
        "OK",
        f"All {len(stats_pos)} position(s) from player stats are covered by dim_positions",
    )]


# ---------------------------------------------------------------------------
# Per-table validation runner
# ---------------------------------------------------------------------------

def validate_dimension(filename: str, pk_col: str) -> tuple:
    path = os.path.join(CLEAN_DIR, filename)

    if not os.path.exists(path):
        return None, [Finding("File exists", "ERROR", f"Not found: {path}")]

    try:
        df = pd.read_csv(path, low_memory=False)
    except Exception as exc:
        return None, [Finding("Load CSV", "ERROR", f"Failed to read: {exc}")]

    findings = []
    findings += chk_shape(df)
    findings += chk_duplicate_pks(df, pk_col)
    findings += chk_missing_values(df)

    # Dimension-specific checks
    if filename == "dim_positions.csv":
        findings += chk_position_groups(df)
        findings += chk_positions_coverage(df)

    if filename == "dim_teams.csv":
        findings += chk_team_count(df)
        findings += chk_teams_coverage(df)

    return df, findings


# ---------------------------------------------------------------------------
# Terminal output
# ---------------------------------------------------------------------------

def print_section(idx: int, filename: str, findings: list) -> None:
    n_errors   = sum(1 for f in findings if f.status == "ERROR")
    n_warnings = sum(1 for f in findings if f.status == "WARNING")

    print(f"\n[{idx}/{len(DIMENSIONS)}] {filename}")
    print()
    for f in findings:
        print(f"  {STATUS_TAG[f.status]}  {f.check}: {f.detail}")

    parts = []
    if n_errors:
        parts.append(f"{n_errors} error(s)")
    if n_warnings:
        parts.append(f"{n_warnings} warning(s)")
    if not parts:
        parts.append("all checks passed")
    print(f"\n         → {', '.join(parts)}")


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------

def build_md_report(all_results: list) -> str:
    lines = []
    now   = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines.append("# Bearlytics — Dimension Table Validation Report")
    lines.append(f"\n_Generated: {now}_\n")
    lines.append("> **Read-only audit. No datasets were modified.**\n")

    # Summary table
    lines.append("## Summary\n")
    lines.append("| # | Dimension Table | Rows | Errors | Warnings | Status |")
    lines.append("|---|-----------------|------|--------|----------|--------|")

    for idx, (filename, _, findings) in enumerate(all_results, 1):
        shape    = next((f for f in findings if f.check == "Shape"), None)
        rows_str = shape.detail.split(" rows")[0] if shape else "—"
        n_err    = sum(1 for f in findings if f.status == "ERROR")
        n_warn   = sum(1 for f in findings if f.status == "WARNING")
        status   = "❌ Errors" if n_err else ("⚠️ Warnings" if n_warn else "✅ Pass")
        lines.append(f"| {idx} | `{filename}` | {rows_str} | {n_err} | {n_warn} | {status} |")

    lines.append("")

    # Per-table detail sections
    for idx, (filename, pk_col, findings) in enumerate(all_results, 1):
        lines.append("---\n")
        lines.append(f"## {idx}. `{filename}`\n")
        lines.append(f"**Primary Key:** `{pk_col}`\n")
        lines.append("| Check | Status | Detail |")
        lines.append("|-------|--------|--------|")
        for f in findings:
            icon   = STATUS_ICON[f.status]
            detail = f.detail.replace("|", "\\|")
            lines.append(f"| {f.check} | {icon} {f.status} | {detail} |")
        lines.append("")

    lines += ["---\n", "_End of report_"]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    os.makedirs(DOCS_DIR, exist_ok=True)

    print("=" * 60)
    print(" BEARLYTICS — DIMENSION TABLE VALIDATION")
    print("=" * 60)

    all_results = []

    for idx, (filename, pk_col) in enumerate(DIMENSIONS.items(), 1):
        _, findings = validate_dimension(filename, pk_col)
        all_results.append((filename, pk_col, findings))
        print_section(idx, filename, findings)

    # Summary table
    print("\n" + "=" * 60)
    print(" SUMMARY")
    print("=" * 60)
    col_w = 30
    print(f"\n  {'Table':<{col_w}}  {'Errors':>6}  {'Warnings':>8}  Status")
    print(f"  {'-'*col_w}  {'-'*6}  {'-'*8}  ------")

    total_errors = total_warnings = 0
    for filename, _, findings in all_results:
        n_err  = sum(1 for f in findings if f.status == "ERROR")
        n_warn = sum(1 for f in findings if f.status == "WARNING")
        total_errors   += n_err
        total_warnings += n_warn
        status = "PASS" if not (n_err or n_warn) else ("ERRORS" if n_err else "WARNINGS")
        print(f"  {filename:<{col_w}}  {n_err:>6}  {n_warn:>8}  {status}")

    print(f"\n  Total: {total_errors} error(s), {total_warnings} warning(s)\n")

    # Markdown report
    md = build_md_report(all_results)
    with open(REPORT_FILE, "w", encoding="utf-8") as fh:
        fh.write(md)
    print(f"  Report saved: {REPORT_FILE}\n")


if __name__ == "__main__":
    main()
