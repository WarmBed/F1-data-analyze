"""檢查衝刺賽週末的可用會話"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import fastf1

sprint_weekends = [
    (2020, "Emilia Romagna"),
    (2021, "Great Britain"),
    (2021, "Italy"),
    (2021, "Brazil"),
    (2022, "Emilia Romagna"),
    (2022, "Austria"),
    (2022, "Brazil"),
    (2023, "Azerbaijan"),
    (2023, "Austria"),
    (2023, "Belgium"),
    (2023, "Qatar"),
    (2023, "United States"),
    (2023, "Brazil"),
    (2024, "China"),
    (2024, "Miami"),
    (2024, "Austria"),
    (2024, "United States"),
    (2024, "Brazil"),
    (2024, "Qatar"),
]

print("=" * 80)
print("衝刺賽週末可用會話檢查")
print("=" * 80)

available_sessions = []

for year, race in sprint_weekends:
    try:
        event = fastf1.get_event(year, race)
        sessions = []
        
        # 檢查各種會話類型
        for session_type in ['FP1', 'FP2', 'FP3', 'Q', 'SQ', 'S', 'R']:
            try:
                session_obj = event.get_session(session_type)
                sessions.append(session_type)
            except:
                pass
        
        print(f"{year} {race:20s} - 可用: {', '.join(sessions)}")
        available_sessions.append((year, race, sessions))
        
    except Exception as e:
        print(f"{year} {race:20s} - 錯誤: {e}")

print("\n" + "=" * 80)
print("建議替代方案")
print("=" * 80)
print("衝刺賽週末格式：FP1 → Q（排位賽）→ SQ（衝刺排位賽）→ S（衝刺賽）→ R（正賽）")
print("\n推薦使用：")
print("  1. FP1 - 唯一的自由練習（最接近 FP3 的訓練性質）")
print("  2. S (Sprint) - 衝刺賽本身（真實比賽數據，但較短）")
print("  3. SQ (Sprint Qualifying) - 衝刺排位賽（類似排位賽）")
