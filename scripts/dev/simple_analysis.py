import json
import traceback

try:
    with open(r'json\LiveF1\2025\Abu_Dhabi_Race\CarData.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    records = data['records']
    result = {
        "total_records": len(records),
        "race_duration_seconds": 7200,
        "avg_sampling_rate_hz": len(records) / 7200
    }
    
    # Sample timestamps
    result["sample_timestamps"] = [rec['timestamp'] for rec in records[1000:1020]]
    
    # Parse timestamp function
    def parse_ts(ts):
        parts = ts.split(':')
        h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
        return h * 3600 + m * 60 + s
    
    # Calculate intervals
    intervals = []
    for i in range(min(2000, len(records) - 1)):
        t1 = parse_ts(records[i]['timestamp'])
        t2 = parse_ts(records[i+1]['timestamp'])
        intervals.append(t2 - t1)
    
    if intervals:
        result["interval_analysis"] = {
            "avg_interval_ms": sum(intervals) / len(intervals) * 1000,
            "min_interval_ms": min(intervals) * 1000,
            "max_interval_ms": max(intervals) * 1000,
            "sampling_rate_hz": 1 / (sum(intervals) / len(intervals))
        }
    
    # Find start reaction times
    start_times = {}
    for rec in records:
        ts = rec['timestamp']
        entries = rec.get('data', {}).get('Entries', [])
        if not entries:
            continue
        cars = entries[0].get('Cars', {})
        for driver_num, driver_data in cars.items():
            if driver_num not in start_times:
                speed = driver_data.get('Channels', {}).get('2', 0)
                rpm = driver_data.get('Channels', {}).get('0', 0)
                if speed > 5 and rpm > 8000:
                    start_times[driver_num] = parse_ts(ts)
    
    if start_times:
        base_time = min(start_times.values())
        sorted_times = sorted(start_times.items(), key=lambda x: x[1])
        result["start_reaction"] = {
            "base_time": base_time,
            "drivers": [{
                "driver": d[0],
                "delta_ms": (d[1] - base_time) * 1000
            } for d in sorted_times[:10]]
        }
    
    result["status"] = "success"
    
except Exception as e:
    result = {
        "status": "error",
        "error": str(e),
        "traceback": traceback.format_exc()
    }

with open(r'result.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
