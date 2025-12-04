"""調試 RaceControlMessages 和 PitLaneTime 數據格式"""
import json
from Live_timing_test.demo_histroy_live_position_tracking import LiveF1DataSource

ds = LiveF1DataSource(
    year=2025, 
    meeting='2025-04-06_Japanese_Grand_Prix', 
    session='2025-04-06_Race'
)
ds.load_all_data()

# 調試 RaceControlMessages
print("=" * 60)
print("RaceControlMessages 調試")
print("=" * 60)

rcm = ds.get_race_control_messages()
print(f"記錄數: {len(rcm) if rcm else 0}")

if rcm:
    for i, record in enumerate(rcm[:5]):
        print(f"\n=== 記錄 {i+1} ===")
        print(f"類型: {type(record)}")
        print(f"內容: {json.dumps(record, indent=2, default=str)}")

