#!/usr/bin/env python3
"""測試 Brake Performance Loader 的檔案搜尋邏輯"""

import glob
import os

# 模擬 loader 的搜尋邏輯
year = 2025
race = "Singapore"
session = "R"

def sanitize_for_filename(value):
    text = str(value or "").strip()
    if not text:
        return "unknown"
    sanitized = []
    for ch in text:
        if ch.isalnum() or ch in {"-", "_"}:
            sanitized.append(ch)
        else:
            sanitized.append("_")
    collapsed = "".join(sanitized)
    while "__" in collapsed:
        collapsed = collapsed.replace("__", "_")
    return collapsed.strip("_") or "value"

race_slug = sanitize_for_filename(race)
session_slug = sanitize_for_filename(session)

patterns = [
    f"all_drivers_brake_performance_{year}_{race}_{session}.json",
    f"all_drivers_brake_performance_{year}_{race_slug}_{session_slug}.json",
    f"all_drivers_brake_performance_*_{race}_{session}.json",
    f"all_drivers_brake_performance_*_{race_slug}_{session_slug}.json",
    f"brake_performance_{year}_{race}_{session}.json",
    f"brake_performance_{year}_{race_slug}_{session_slug}.json",
]

print("=" * 80)
print("Brake Performance 檔案搜尋測試")
print("=" * 80)
print(f"\n參數:")
print(f"  Year: {year}")
print(f"  Race: {race}")
print(f"  Session: {session}")
print(f"  Race Slug: {race_slug}")
print(f"  Session Slug: {session_slug}")

print(f"\n搜尋模式:")
for i, pattern in enumerate(patterns, 1):
    print(f"  {i}. {pattern}")

print(f"\n實際檔案:")
actual_files = glob.glob("json/brake_performance_*.json")
for f in actual_files:
    print(f"  ✅ {f}")

print(f"\n匹配測試:")
for i, pattern in enumerate(patterns, 1):
    full_pattern = f"json/{pattern}"
    matches = glob.glob(full_pattern)
    if matches:
        print(f"  ✅ 模式 {i} 匹配: {len(matches)} 個檔案")
        for match in matches:
            print(f"     → {match}")
    else:
        print(f"  ❌ 模式 {i} 無匹配")

print("\n" + "=" * 80)
print("診斷結果:")
print("=" * 80)

# 檢查預期的檔案名稱
expected_file = f"json/brake_performance_{year}_{race}_{session}.json"
if os.path.exists(expected_file):
    print(f"✅ 檔案存在: {expected_file}")
    print(f"   大小: {os.path.getsize(expected_file)} bytes")
else:
    print(f"❌ 檔案不存在: {expected_file}")

# 檢查其他可能的名稱
alternative = f"json/all_drivers_brake_performance_{year}_{race}_{session}.json"
if os.path.exists(alternative):
    print(f"✅ 替代檔案存在: {alternative}")
    print(f"   大小: {os.path.getsize(alternative)} bytes")
