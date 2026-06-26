#!/usr/bin/env python3
"""
create_date_dimension.py

Generates a date dimension table for Power BI covering every calendar day
from 2016-01-01 through 2025-12-31.

Output:
  03_clean_data/date_dimension.csv
"""

import os
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CLEAN_DIR  = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "03_clean_data"))
OUTPUT     = os.path.join(CLEAN_DIR, "date_dimension.csv")

# Generate a DatetimeIndex for every day in the range
dates = pd.date_range(start="2016-01-01", end="2025-12-31", freq="D")

df = pd.DataFrame({
    "Date":       dates.strftime("%Y-%m-%d"),
    "Year":       dates.year,
    "Season":     dates.year,                        # Season equals Year per spec
    "Quarter":    dates.quarter,
    "Month":      dates.month,
    "Month_Name": dates.strftime("%B"),              # e.g. January, February
    "Week":       dates.isocalendar().week.astype(int),  # ISO week number 1–53
    "Day":        dates.day,
    "Day_Name":   dates.strftime("%A"),              # e.g. Monday, Tuesday
    "Is_Weekend": dates.dayofweek >= 5,              # Saturday=5, Sunday=6
})

os.makedirs(CLEAN_DIR, exist_ok=True)
df.to_csv(OUTPUT, index=False)

print(f"Total rows : {len(df):,}")
print(f"Date range : {df['Date'].iloc[0]}  →  {df['Date'].iloc[-1]}")
print(f"Saved      : {OUTPUT}")
