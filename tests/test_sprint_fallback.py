"""測試衝刺賽週末會話切換邏輯"""
import sys
sys.path.insert(0, '.')
from batch_cli_executor import BatchCLIExecutor

# 創建執行器實例
executor = BatchCLIExecutor(
    functions=[1],
    years=[2024],
    sessions=["FP3"],
    skip_existing=True,
    verbose=True
)

# 測試衝刺賽週末檢測
test_cases = [
    (2024, "Qatar", "FP3"),      # 衝刺賽週末
    (2024, "Japan", "FP3"),      # 普通週末
    (2023, "Austria", "FP3"),    # 衝刺賽週末
    (2022, "Monaco", "FP3"),     # 普通週末
]

print("=" * 80)
print("衝刺賽週末會話切換測試")
print("=" * 80)

for year, race, session in test_cases:
    is_sprint = executor.is_sprint_weekend(year, race)
    fallback = executor.get_fallback_session(year, race, session)
    
    status = "✅ 衝刺週末" if is_sprint else "  普通週末"
    action = f" → {fallback}" if fallback != session else ""
    
    print(f"{year} {race:20s} {session} {status}{action}")

print("\n" + "=" * 80)
print("建立任務列表測試（2024 Qatar）")
print("=" * 80)

# 建立任務
tasks = []
for race in ["Qatar", "Japan"]:
    for session in ["FP3"]:
        actual_session = executor.get_fallback_session(2024, race, session)
        tasks.append({
            "year": 2024,
            "race": race,
            "session": actual_session,
            "original_session": session if actual_session != session else None
        })

for task in tasks:
    original = f" (替代 {task['original_session']})" if task['original_session'] else ""
    print(f"2024 {task['race']:20s} {task['session']}{original}")
