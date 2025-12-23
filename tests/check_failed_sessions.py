"""檢查 F1 批次生成失敗的 session 原因"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import fastf1

failed_sessions = [
    (2019, "Japan", "FP3"),
    (2020, "Styria", "FP3"),
    (2020, "Emilia Romagna", "FP3"),
    (2021, "Great Britain", "FP3"),
    (2021, "Italy", "FP3"),
    (2021, "Russia", "FP3"),
    (2021, "Brazil", "FP3"),
    (2022, "Emilia Romagna", "FP3"),
    (2022, "Austria", "FP3"),
    (2022, "Brazil", "FP3"),
    (2023, "Azerbaijan", "FP3"),
    (2023, "Austria", "FP3"),
    (2023, "Belgium", "FP3"),
    (2023, "Qatar", "FP3"),
    (2023, "United States", "FP3"),
    (2023, "Brazil", "FP3"),
    (2024, "China", "FP3"),
    (2024, "Miami", "FP3"),
    (2024, "Austria", "FP3"),
    (2024, "United States", "FP3"),
    (2024, "Brazil", "FP3"),
    (2024, "Qatar", "FP3"),
]

print("=" * 80)
print("檢查失敗的 Session")
print("=" * 80)

no_fp3_sessions = []
other_errors = []

for year, race, session in failed_sessions:
    try:
        event = fastf1.get_event(year, race)
        # 檢查是否有 FP3
        try:
            session_obj = event.get_session('FP3')
            other_errors.append((year, race, "其他錯誤（session 存在）"))
            print(f"❓ {year} {race:20s} FP3 - session 存在但失敗")
        except ValueError as e:
            if "does not exist" in str(e):
                no_fp3_sessions.append((year, race))
                print(f"❌ {year} {race:20s} FP3 - 沒有 FP3（衝刺賽週末）")
            else:
                raise
    except Exception as e:
        other_errors.append((year, race, str(e)))
        print(f"⚠️  {year} {race:20s} FP3 - 錯誤: {e}")

print("\n" + "=" * 80)
print("統計結果")
print("=" * 80)
print(f"沒有 FP3 的賽事: {len(no_fp3_sessions)} 個")
print(f"其他錯誤: {len(other_errors)} 個")

if no_fp3_sessions:
    print("\n沒有 FP3 的賽事列表（衝刺賽週末）：")
    for year, race in no_fp3_sessions:
        print(f"  - {year} {race}")
