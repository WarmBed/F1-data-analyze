"""
Extract Hamilton Lap 10 speed samples from Live Timing CarData.z stream
and compare them against the processed fastf1 telemetry slice.
"""
from __future__ import annotations

import base64
import json
import zlib
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

FASTF1_CSV = Path("Live_timing_test/HAM_Lap10_telemetry.csv")
LIVETIMING_CSV = Path("Live_timing_test/ham_lap10_livetiming_filtered.csv")
COMPARISON_CSV = Path("Live_timing_test/ham_lap10_speed_comparison.csv")
CAR_DATA_URL = (
    "https://livetiming.formula1.com/static/2025/2025-04-06_Japanese_Grand_Prix/"
    "2025-04-06_Race/CarData.z.jsonStream"
)

# Official channel identifiers from FIA Live Timing CarData stream
CHANNEL_ID_MAP = {
    "0": "rpm",          # Engine RPM
    "2": "speed",        # Car speed in km/h
    "3": "gear",         # Current gear (1-8, N, R)
    "4": "throttle",     # Throttle position %
    "5": "brake",        # Brake state %
    "45": "drs",         # DRS state
}

def read_fastf1_slice() -> pd.DataFrame:
    fast_df = pd.read_csv(FASTF1_CSV, parse_dates=["Date"])
    fast_df["Date"] = fast_df["Date"].dt.tz_localize("UTC")
    fast_df["TimeOffset"] = (fast_df["Date"] - fast_df["Date"].min()).dt.total_seconds()
    return fast_df

def decode_stream_line(payload: str) -> dict | None:
    try:
        decoded_bytes = base64.b64decode(payload)
        data = zlib.decompress(decoded_bytes, wbits=-15)
        return json.loads(data.decode("utf-8"))
    except Exception:
        return None

def extract_lap_window(fast_df: pd.DataFrame) -> pd.DataFrame:
    start_ts = fast_df["Date"].min()
    end_ts = fast_df["Date"].max()
    print(f"FastF1 Lap10 timeframe (UTC): {start_ts} -> {end_ts}")

    print("Downloading Live Timing CarData stream...")
    response = requests.get(CAR_DATA_URL, timeout=120)
    response.raise_for_status()
    lines = [line for line in response.content.decode("utf-8-sig").split("\r\n") if line]
    print(f"Total stream lines: {len(lines)}")

    records: list[dict] = []
    for line in lines:
        if len(line) < 13:
            continue
        decoded = decode_stream_line(line[12:])
        if not decoded:
            continue
        for entry in decoded.get("Entries", []):
            utc_str = entry.get("Utc")
            if not utc_str:
                continue
            utc_dt = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
            if utc_dt < start_ts or utc_dt > end_ts:
                continue
            car44 = entry.get("Cars", {}).get("44")
            if not car44:
                continue
            channels = car44.get("Channels", {})
            record = {"Utc": utc_dt}
            for channel_id, column_name in CHANNEL_ID_MAP.items():
                record[column_name] = channels.get(channel_id)
            records.append(record)

    if not records:
        raise RuntimeError("No Live Timing samples found inside the Lap 10 window")

    live_df = pd.DataFrame(records).sort_values("Utc").reset_index(drop=True)
    numeric_cols = list(CHANNEL_ID_MAP.values())
    live_df[numeric_cols] = live_df[numeric_cols].apply(pd.to_numeric, errors="coerce")
    live_df["TimeOffset"] = (live_df["Utc"] - live_df["Utc"].min()).dt.total_seconds()
    return live_df

def align_samples(live_df: pd.DataFrame, fast_df: pd.DataFrame) -> pd.DataFrame:
    fast_series = fast_df.set_index("TimeOffset")["Speed"].sort_index()
    aligned_rows: list[dict] = []

    for _, row in live_df.iterrows():
        time_offset = row["TimeOffset"]
        idx = fast_series.index.searchsorted(time_offset)
        candidates = []
        if idx < len(fast_series.index):
            candidates.append((fast_series.index[idx], float(fast_series.iloc[idx])))
        if idx > 0:
            candidates.append((fast_series.index[idx - 1], float(fast_series.iloc[idx - 1])))
        if not candidates:
            continue
        best_time, best_speed = min(candidates, key=lambda x: abs(x[0] - time_offset))
        if abs(best_time - time_offset) <= 0.05:  # within 50 ms
            speed_val = row["speed"]
            if pd.isna(speed_val):
                continue
            aligned_rows.append(
                {
                    "Utc": row["Utc"],
                    "TimeOffset": time_offset,
                    "FastMatchedOffset": best_time,
                    "LiveTimingSpeed": speed_val,
                    "FastF1Speed": best_speed,
                    "Diff": speed_val - best_speed,
                }
            )

    if not aligned_rows:
        raise RuntimeError("No overlapping samples within 50 ms tolerance")

    return pd.DataFrame(aligned_rows)

def main() -> None:
    fast_df = read_fastf1_slice()
    live_df = extract_lap_window(fast_df)
    live_df.to_csv(LIVETIMING_CSV, index=False)
    print(f"Saved Live Timing slice to {LIVETIMING_CSV}")

    aligned_df = align_samples(live_df, fast_df)
    aligned_df.to_csv(COMPARISON_CSV, index=False)
    print(f"Saved aligned comparison samples to {COMPARISON_CSV}")

    print("\nSummary metrics:")
    if live_df["speed"].notna().any():
        speed_min = live_df["speed"].min()
        speed_max = live_df["speed"].max()
        speed_summary = f"speed range {speed_min:.1f}-{speed_max:.1f} km/h"
    else:
        speed_summary = "no valid speed samples"

    print(f"  Live Timing samples: {len(live_df)} ({speed_summary})")
    print(
        f"  fastf1 samples: {fast_df['Speed'].count()} "
        f"(speed range {fast_df['Speed'].min():.1f}-{fast_df['Speed'].max():.1f} km/h)"
    )
    print(f"  Overlapping aligned samples: {len(aligned_df)}")
    print(f"  Mean delta (Live Timing - fastf1): {aligned_df['Diff'].mean():.2f} km/h")
    print(f"  Max abs delta: {aligned_df['Diff'].abs().max():.2f} km/h")

if __name__ == "__main__":
    main()
