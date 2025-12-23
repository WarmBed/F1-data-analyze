import argparse
import pickle
from pathlib import Path
from typing import Any


def _summarize_dict(d: dict, label: str, max_keys: int = 80) -> None:
    keys = list(d.keys())
    print(f"{label}: dict with {len(keys)} keys")
    print("  keys(sample)=", sorted(keys)[:max_keys])


def _inspect_snapshot_dict(snapshot: dict) -> None:
    _summarize_dict(snapshot, "snapshot[0]")

    # common time fields (best-effort)
    for tk in [
        "race_time_seconds",
        "race_time",
        "session_time",
        "t",
        "timestamp",
        "time",
    ]:
        if tk in snapshot:
            tv = snapshot[tk]
            print(f"  time field '{tk}': type={type(tv)} value_sample={tv}")

    # Look for per-driver structures
    for dk in [
        "drivers",
        "cars",
        "driver_data",
        "positions",
        "telemetry",
        "track_status",
        "race_control",
        "weather",
    ]:
        if dk not in snapshot:
            continue

        dv = snapshot[dk]
        print(f"  nested '{dk}' type=", type(dv))

        if isinstance(dv, dict):
            dkeys = list(dv.keys())
            print(f"    nested '{dk}' keys(sample)=", dkeys[:15])
            if dkeys:
                sample_key = dkeys[0]
                sample_val = dv[sample_key]
                print("    sample key=", sample_key, "type=", type(sample_val))
                if isinstance(sample_val, dict):
                    _summarize_dict(sample_val, f"    sample '{dk}'[{sample_key}]")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect Live Timing PKL schema")
    parser.add_argument(
        "pkl_path",
        nargs="?",
        default="data/live_timing_cache/2025/2025_Abu_Dhabi_Race.pkl",
        help="Path to a Live Timing PKL file",
    )
    args = parser.parse_args()

    pkl_path = Path(args.pkl_path)
    print("PKL:", pkl_path, "exists=", pkl_path.exists())
    if not pkl_path.exists():
        raise SystemExit(2)

    print("size_bytes=", pkl_path.stat().st_size)
    with pkl_path.open("rb") as f:
        obj: Any = pickle.load(f)

    print("\nTop-level type:", type(obj))
    if not isinstance(obj, dict):
        public_attrs = [a for a in dir(obj) if not a.startswith("_")]
        print("Non-dict top-level; public attrs sample:", public_attrs[:80])
        return

    _summarize_dict(obj, "Top-level")

    list_keys = [k for k, v in obj.items() if isinstance(v, list)]
    print("\nTop-level list keys:", list_keys)

    candidate_keys = [k for k in ["snapshots", "aligned_snapshots", "frames", "data"] if k in obj]
    if not candidate_keys and list_keys:
        candidate_keys = sorted(list_keys)

    for key in candidate_keys[:6]:
        v = obj[key]
        print(f"\n=== Inspect key: {key} ===")
        print("type=", type(v))

        if isinstance(v, list):
            print("len=", len(v))
            if v:
                first = v[0]
                print("[0] type=", type(first))
                if isinstance(first, dict):
                    _inspect_snapshot_dict(first)
        elif isinstance(v, dict):
            _summarize_dict(v, f"key '{key}'")

    # Also inspect other important list sections beyond snapshots
    for key in [
        "track_status",
        "race_control_messages",
        "weather_data",
        "pit_events",
        "tyre_timestamps",
    ]:
        if key not in obj or not isinstance(obj[key], list):
            continue
        v = obj[key]
        print(f"\n=== Inspect key: {key} (summary) ===")
        print("type=", type(v), "len=", len(v))
        if not v:
            continue
        first = v[0]
        print("[0] type=", type(first))
        if isinstance(first, dict):
            _summarize_dict(first, f"{key}[0]")

            if "data" in first:
                data_val = first["data"]
                print(f"  {key}[0]['data'] type=", type(data_val))
                if isinstance(data_val, dict):
                    print(f"  {key}[0]['data'] keys(sample)=", sorted(data_val.keys())[:60])
                elif isinstance(data_val, list):
                    print(f"  {key}[0]['data'] len=", len(data_val))
                    if data_val:
                        print(f"  {key}[0]['data'][0] type=", type(data_val[0]))
                        print(f"  {key}[0]['data'][0] value_sample=", data_val[0])
        else:
            print("[0] value_sample=", first)


if __name__ == "__main__":
    main()
