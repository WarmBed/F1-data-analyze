"""測試 Chase Strategy 工作空間映射 - 完整驗證"""

from core.workspace_serializer import WorkspaceSerializer
import re

print("=" * 70)
print("Chase Strategy 工作空間映射完整驗證")
print("=" * 70)

# ============================================================================
# 步驟 1: 檢查 WINDOW_TYPE_MAPPING（類別名稱 → 類型標識）
# ============================================================================
print("\n[步驟 1] WINDOW_TYPE_MAPPING 檢查")
print("-" * 70)

WINDOW_TYPE_MAPPING = WorkspaceSerializer.WINDOW_TYPE_MAPPING

if "ChaseStrategyMDI" in WINDOW_TYPE_MAPPING:
    mapping_value = WINDOW_TYPE_MAPPING["ChaseStrategyMDI"]
    status = "[✅ PASS]" if mapping_value == "live_chase_strategy" else f"[❌ FAIL] 值應為 'live_chase_strategy'，實際為 '{mapping_value}'"
    print(f"{status} ChaseStrategyMDI -> {mapping_value}")
else:
    print("[❌ FAIL] ChaseStrategyMDI 未在 WINDOW_TYPE_MAPPING 中")

# ============================================================================
# 步驟 2: 檢查 title_to_type_map（視窗標題 → 類型標識）
# ============================================================================
print("\n[步驟 2] title_to_type_map 檢查")
print("-" * 70)

# 讀取 workspace_serializer.py 檔案內容
with open("core/workspace_serializer.py", "r", encoding="utf-8") as f:
    content = f.read()

# 提取 title_to_type_map 的定義
title_map_match = re.search(
    r'title_to_type_map\s*=\s*\{([^}]+)\}',
    content,
    re.DOTALL
)

if title_map_match:
    title_map_content = title_map_match.group(1)
    
    # 檢查 "Chase Strategy": "live_chase_strategy"
    if '"Chase Strategy": "live_chase_strategy"' in title_map_content:
        print('[✅ PASS] "Chase Strategy": "live_chase_strategy" 已存在')
    else:
        print('[❌ FAIL] "Chase Strategy" 映射未找到或值不正確')
    
    # 顯示所有 Live Timing 映射
    print("\n所有 Live Timing 標題映射:")
    for line in title_map_content.split('\n'):
        if 'live_' in line and ':' in line:
            print(f"  {line.strip()}")
else:
    print("[❌ FAIL] 無法找到 title_to_type_map 定義")

# ============================================================================
# 步驟 3: 檢查 live_timing_name_map（類型標識 → 模組名稱）
# ============================================================================
print("\n[步驟 3] live_timing_name_map 檢查")
print("-" * 70)

# 提取 live_timing_name_map 的定義
name_map_match = re.search(
    r'live_timing_name_map\s*=\s*\{([^}]+)\}',
    content,
    re.DOTALL
)

if name_map_match:
    name_map_content = name_map_match.group(1)
    
    # 檢查 "live_chase_strategy": "Chase Strategy"
    if '"live_chase_strategy": "Chase Strategy"' in name_map_content:
        print('[✅ PASS] "live_chase_strategy": "Chase Strategy" 已存在')
    else:
        print('[❌ FAIL] "live_chase_strategy" 映射未找到或值不正確')
    
    # 顯示所有 Live Timing 映射
    print("\n所有 Live Timing 名稱映射:")
    for line in name_map_content.split('\n'):
        if '"live_' in line and ':' in line:
            print(f"  {line.strip()}")
else:
    print("[❌ FAIL] 無法找到 live_timing_name_map 定義")

# ============================================================================
# 步驟 4: 比對 Driver Strategy（參考對照）
# ============================================================================
print("\n[步驟 4] 與 Driver Strategy 比對")
print("-" * 70)

print("Chase Strategy 映射:")
print(f"  WINDOW_TYPE_MAPPING:  ChaseStrategyMDI -> {WINDOW_TYPE_MAPPING.get('ChaseStrategyMDI', 'NOT FOUND')}")
print(f"  title_to_type_map:    'Chase Strategy' -> live_chase_strategy")
print(f"  live_timing_name_map: live_chase_strategy -> 'Chase Strategy'")

print("\nDriver Strategy 映射 (參考):")
print(f"  WINDOW_TYPE_MAPPING:  LiveTimingDriverStrategy -> {WINDOW_TYPE_MAPPING.get('LiveTimingDriverStrategy', 'NOT FOUND')}")
print(f"  title_to_type_map:    'Driver Strategy' -> live_driver_strategy")
print(f"  live_timing_name_map: live_driver_strategy -> 'Driver Strategy'")

# ============================================================================
# 總結
# ============================================================================
print("\n" + "=" * 70)
print("驗證總結")
print("=" * 70)

tests = [
    ("WINDOW_TYPE_MAPPING", "ChaseStrategyMDI" in WINDOW_TYPE_MAPPING and WINDOW_TYPE_MAPPING["ChaseStrategyMDI"] == "live_chase_strategy"),
    ("title_to_type_map", '"Chase Strategy": "live_chase_strategy"' in content),
    ("live_timing_name_map", '"live_chase_strategy": "Chase Strategy"' in content),
]

passed = sum(1 for _, result in tests if result)
total = len(tests)

for test_name, result in tests:
    status = "[✅]" if result else "[❌]"
    print(f"{status} {test_name}")

print("\n" + "=" * 70)
if passed == total:
    print(f"✅ 全部通過！({passed}/{total})")
    print("Chase Strategy 工作空間序列化/反序列化應該可以正常運作")
else:
    print(f"⚠️ 部分失敗 ({passed}/{total})")
    print("請檢查失敗的映射")
print("=" * 70)
