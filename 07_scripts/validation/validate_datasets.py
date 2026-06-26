#!/usr/bin/env python3
"""
validate_datasets.py

Phase 2 — Bearlytics data quality audit.

Reads each master CSV in 03_clean_data/ and runs structured checks.
DOES NOT modify any dataset — reporting only.

Checks performed per dataset:
  1.  Row and column count
  2.  Duplicate rows
  3.  Duplicate primary keys
  4.  Missing / blank values
  5.  Season range (must be 2016–2025)
  6.  Numeric column type verification
  7.  Bears team abbreviation standardization (CHI)
  8.  Player name whitespace

Outputs:
  Terminal:  formatted findings per dataset + summary table
  07_documentation/data_validation_report.md
"""

import os
import sys
from datetime import datetime

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CLEAN_DIR  = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "03_clean_data"))
DOCS_DIR   = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "07_documentation"))

SEASON_MIN = 2016
SEASON_MAX = 2025

# ---------------------------------------------------------------------------
# Dataset configuration
# ---------------------------------------------------------------------------
# pk              — columns that together form a unique row identifier
# season_col      — name of the season column (checked for 2016–2025 range)
# bears_team_col  — Team column in Bears-only files (all values must be 'CHI')
#                   Set to None for multi-team files (league stats).
# numeric_cols    — columns that must contain numeric values
# known_blank_cols— columns intentionally left blank due to source limitations;
#                   missing-value warnings are suppressed (reported as INFO)

DATASETS: dict = {
    "bears_team_stats_2016_2025.csv": {
        "description": "Chicago Bears season-level team statistics (2016–2025)",
        "pk": ["Season"],
        "season_col": "Season",
        "bears_team_col": None,
        "numeric_cols": [
            "Season", "Wins", "Losses", "Ties",
            "Points_For", "Points_Against", "Point_Differential", "Games_Played",
            "Passing_Yards", "Rushing_Yards", "Total_Offense_Yards",
            "Passing_TDs", "Rushing_TDs", "Total_TDs",
            "Turnovers", "Takeaways", "Turnover_Differential",
        ],
        "known_blank_cols": [],
    },
    "bears_game_logs_2016_2025.csv": {
        "description": "Chicago Bears game-by-game results (2016–2025)",
        "pk": ["Season", "Week"],
        "season_col": "Season",
        "bears_team_col": None,
        "numeric_cols": [
            "Season", "Week",
            "Points_For", "Points_Against", "Point_Differential",
            "Wins_After_Game", "Losses_After_Game", "Ties_After_Game",
        ],
        "known_blank_cols": [],
    },
    "bears_player_stats_2016_2025.csv": {
        "description": "Chicago Bears individual player statistics (2016–2025)",
        "pk": ["Season", "Player_Name"],
        "season_col": "Season",
        "bears_team_col": "Team",
        "numeric_cols": [
            "Season", "Games_Played",
            "Passing_Yards", "Passing_TDs", "Interceptions_Thrown",
            "Rushing_Yards", "Rushing_TDs",
            "Receiving_Yards", "Receiving_TDs", "Receptions", "Targets",
            "Total_Yards", "Total_TDs",
        ],
        # Position cannot be inferred from play-by-play data — intentionally blank
        "known_blank_cols": ["Position"],
    },
    "bears_salary_data_2016_2025.csv": {
        "description": "Chicago Bears player contract data (signed through ~April 2022)",
        "pk": ["Season", "Player_Name"],
        "season_col": "Season",
        "bears_team_col": "Team",
        "numeric_cols": [
            "Season", "Contract_Value", "Guaranteed_Money", "Contract_Length_Years",
        ],
        # Per-season cap breakdown not available from any free source — see build script
        "known_blank_cols": [
            "Age", "Cap_Hit", "Base_Salary", "Signing_Bonus", "Roster_Bonus", "Dead_Cap",
        ],
    },
    "nfl_league_stats_2016_2025.csv": {
        "description": "League-wide season statistics for all NFL teams (2016–2025)",
        "pk": ["Season", "Team"],
        "season_col": "Season",
        "bears_team_col": None,
        "numeric_cols": [
            "Season", "Wins", "Losses", "Ties", "Win_Percentage",
            "Points_For", "Points_Against", "Point_Differential",
            "Passing_Yards", "Rushing_Yards", "Total_Offense_Yards",
            "Passing_TDs", "Rushing_TDs",
            "Turnovers", "Takeaways", "Turnover_Differential",
            "Offensive_Rank", "Defensive_Rank",
        ],
        "known_blank_cols": [],
    },
}

# ---------------------------------------------------------------------------
# Finding type
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
# Individual check functions
# ---------------------------------------------------------------------------

def chk_shape(df: pd.DataFrame) -> list:
    return [Finding("Shape", "INFO", f"{len(df):,} rows × {len(df.columns)} columns")]


def chk_duplicate_rows(df: pd.DataFrame) -> list:
    n = int(df.duplicated().sum())
    if n:
        return [Finding("Duplicate rows", "WARNING", f"{n} exact duplicate rows")]
    return [Finding("Duplicate rows", "OK", "No exact duplicate rows")]


def chk_duplicate_pks(df: pd.DataFrame, pk_cols: list) -> list:
    present = [c for c in pk_cols if c in df.columns]
    if not present:
        return [Finding("Duplicate PKs", "WARNING", f"PK columns not found: {pk_cols}")]
    n = int(df.duplicated(subset=present).sum())
    label = ", ".join(present)
    if n:
        return [Finding("Duplicate PKs", "ERROR", f"{n} duplicate primary keys ({label})")]
    return [Finding("Duplicate PKs", "OK", f"No duplicate primary keys ({label})")]


def chk_missing_values(df: pd.DataFrame, known_blank_cols: list) -> list:
    findings = []
    has_unexpected_missing = False

    for col in df.columns:
        null_count = int(df[col].isnull().sum())

        # Count empty-string values in non-null object cells
        blank_count = 0
        if df[col].dtype == object:
            non_null = df[col].dropna()
            blank_count = int((non_null.astype(str).str.strip() == "").sum())

        total = null_count + blank_count
        if total == 0:
            continue

        pct = total / len(df) * 100

        if col in known_blank_cols:
            findings.append(Finding(
                f"Missing: {col}",
                "INFO",
                f"{total:,}/{len(df):,} ({pct:.0f}%) — intentionally blank (source limitation)",
            ))
        else:
            has_unexpected_missing = True
            findings.append(Finding(
                f"Missing: {col}",
                "WARNING",
                f"{total:,}/{len(df):,} ({pct:.1f}%) missing or blank",
            ))

    if not has_unexpected_missing:
        findings.insert(0, Finding("Missing values", "OK", "No unexpected missing or blank values"))

    return findings


def chk_season_range(df: pd.DataFrame, season_col: str) -> list:
    if season_col not in df.columns:
        return [Finding("Season range", "WARNING", f"Column '{season_col}' not found")]

    seasons = pd.to_numeric(df[season_col], errors="coerce")
    bad_mask = seasons.isna() | (seasons < SEASON_MIN) | (seasons > SEASON_MAX)
    n_bad = int(bad_mask.sum())

    if n_bad:
        bad_vals = sorted(df.loc[bad_mask, season_col].unique().tolist())
        return [Finding("Season range", "ERROR", f"{n_bad} rows outside {SEASON_MIN}–{SEASON_MAX}: {bad_vals}")]

    unique = sorted(df[season_col].dropna().unique().tolist())
    return [Finding("Season range", "OK", f"All in range {SEASON_MIN}–{SEASON_MAX}; seasons: {unique}")]


def chk_numeric_columns(df: pd.DataFrame, numeric_cols: list, known_blank_cols: list) -> list:
    findings = []

    for col in numeric_cols:
        if col not in df.columns:
            findings.append(Finding(f"Numeric: {col}", "WARNING", f"Column not found in dataset"))
            continue

        if col in known_blank_cols:
            continue  # Covered by the missing-values check

        series = df[col]

        if pd.api.types.is_numeric_dtype(series):
            findings.append(Finding(f"Numeric: {col}", "OK", f"dtype={series.dtype}"))
            continue

        # Object dtype — attempt coercion on non-empty values
        non_empty = series.dropna()
        non_empty = non_empty[non_empty.astype(str).str.strip() != ""]
        if non_empty.empty:
            continue  # Entirely blank; covered by missing-values check

        coerced = pd.to_numeric(non_empty, errors="coerce")
        bad = non_empty[coerced.isna()]

        if len(bad):
            sample = bad.head(5).tolist()
            findings.append(Finding(
                f"Numeric: {col}",
                "ERROR",
                f"{len(bad)} non-numeric values — e.g. {sample}",
            ))
        else:
            findings.append(Finding(
                f"Numeric: {col}",
                "WARNING",
                f"Stored as object dtype but values parse as numbers — dtype={series.dtype}",
            ))

    return findings


def chk_team_abbreviation(df: pd.DataFrame, bears_team_col, filename: str) -> list:
    if bears_team_col is None:
        # Multi-team dataset — verify CHI is present somewhere
        if "Team" not in df.columns:
            return []
        chi_rows = int((df["Team"] == "CHI").sum())
        if chi_rows:
            return [Finding("CHI in dataset", "OK", f"CHI appears in {chi_rows} rows")]
        return [Finding("CHI in dataset", "WARNING", "CHI not found in Team column")]

    # Bears-only dataset — all Team values must be 'CHI'
    if bears_team_col not in df.columns:
        return [Finding("Team abbreviation", "WARNING", f"Column '{bears_team_col}' not found")]

    non_chi = df[df[bears_team_col].astype(str).str.strip() != "CHI"]
    if len(non_chi):
        variants = non_chi[bears_team_col].unique().tolist()
        return [Finding("Team abbreviation", "WARNING",
                        f"{len(non_chi)} rows with non-CHI values: {variants}")]
    return [Finding("Team abbreviation", "OK", "All Team values are 'CHI'")]


def chk_player_names(df: pd.DataFrame) -> list:
    if "Player_Name" not in df.columns:
        return []

    col = df["Player_Name"].astype(str)
    findings = []

    # Leading / trailing whitespace
    leading_trailing = (col.str.strip() != col).sum()
    if leading_trailing:
        findings.append(Finding(
            "Player name whitespace",
            "WARNING",
            f"{int(leading_trailing)} values have leading/trailing whitespace",
        ))

    # Consecutive spaces
    double_space = col.str.contains("  ", regex=False).sum()
    if double_space:
        findings.append(Finding(
            "Player name double spaces",
            "WARNING",
            f"{int(double_space)} values contain consecutive spaces",
        ))

    if not findings:
        findings.append(Finding("Player names", "OK", "No whitespace issues in Player_Name"))

    return findings


# ---------------------------------------------------------------------------
# Run all checks for one dataset
# ---------------------------------------------------------------------------

def validate_dataset(filename: str, config: dict) -> tuple:
    path = os.path.join(CLEAN_DIR, filename)

    if not os.path.exists(path):
        return None, [Finding("File exists", "ERROR", f"Not found: {path}")]

    try:
        df = pd.read_csv(path, low_memory=False)
    except Exception as exc:
        return None, [Finding("Load CSV", "ERROR", f"Failed to read: {exc}")]

    findings = []
    findings += chk_shape(df)
    findings += chk_duplicate_rows(df)
    findings += chk_duplicate_pks(df, config["pk"])
    findings += chk_missing_values(df, config["known_blank_cols"])
    findings += chk_season_range(df, config["season_col"])
    findings += chk_numeric_columns(df, config["numeric_cols"], config["known_blank_cols"])
    findings += chk_team_abbreviation(df, config["bears_team_col"], filename)
    findings += chk_player_names(df)

    return df, findings


# ---------------------------------------------------------------------------
# Terminal output
# ---------------------------------------------------------------------------

def print_dataset_section(idx: int, filename: str, config: dict, findings: list) -> None:
    n_errors   = sum(1 for f in findings if f.status == "ERROR")
    n_warnings = sum(1 for f in findings if f.status == "WARNING")

    print(f"\n[{idx}/{len(DATASETS)}] {filename}")
    print(f"       {config['description']}")
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
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines.append("# Bearlytics — Data Validation Report")
    lines.append(f"\n_Generated: {now}_\n")
    lines.append("> **Read-only audit. No datasets were modified.**\n")

    # Summary table
    lines.append("## Summary\n")
    lines.append("| # | Dataset | Rows | Errors | Warnings | Status |")
    lines.append("|---|---------|------|--------|----------|--------|")

    for idx, (filename, config, findings) in enumerate(all_results, 1):
        shape = next((f for f in findings if f.check == "Shape"), None)
        rows_str = shape.detail.split(" rows")[0] if shape else "—"
        n_err  = sum(1 for f in findings if f.status == "ERROR")
        n_warn = sum(1 for f in findings if f.status == "WARNING")
        if n_err:
            status = "❌ Errors"
        elif n_warn:
            status = "⚠️ Warnings"
        else:
            status = "✅ Pass"
        lines.append(f"| {idx} | `{filename}` | {rows_str} | {n_err} | {n_warn} | {status} |")

    lines.append("")

    # Per-dataset detail sections
    for idx, (filename, config, findings) in enumerate(all_results, 1):
        lines.append("---\n")
        lines.append(f"## {idx}. `{filename}`\n")
        lines.append(f"**{config['description']}**\n")
        lines.append(f"**Primary Key:** {', '.join(config['pk'])}\n")

        lines.append("| Check | Status | Detail |")
        lines.append("|-------|--------|--------|")

        for f in findings:
            icon   = STATUS_ICON[f.status]
            detail = f.detail.replace("|", "\\|")
            lines.append(f"| {f.check} | {icon} {f.status} | {detail} |")

        lines.append("")

    lines.append("---\n")
    lines.append("_End of report_")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    os.makedirs(DOCS_DIR, exist_ok=True)

    print("=" * 64)
    print(" BEARLYTICS — DATA VALIDATION")
    print("=" * 64)

    all_results = []

    for idx, (filename, config) in enumerate(DATASETS.items(), 1):
        _, findings = validate_dataset(filename, config)
        all_results.append((filename, config, findings))
        print_dataset_section(idx, filename, config, findings)

    # Summary table
    print("\n" + "=" * 64)
    print(" SUMMARY")
    print("=" * 64)
    col_w = 44
    print(f"\n  {'Dataset':<{col_w}}  {'Errors':>6}  {'Warnings':>8}  Status")
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
    report_path = os.path.join(DOCS_DIR, "data_validation_report.md")
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(md)
    print(f"  Report saved: {report_path}\n")


if __name__ == "__main__":
    main()
