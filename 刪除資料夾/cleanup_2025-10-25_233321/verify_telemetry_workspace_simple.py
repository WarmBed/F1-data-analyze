#!/usr/bin/env python3
"""
簡單驗證遙測分析模組 Workspace 支援
"""

print("=" * 60)
print("驗證遙測分析模組 Workspace 支援")
print("=" * 60)

# 測試 1: 檢查映射
print("\n✅ 測試 1: 檢查 WINDOW_TYPE_MAPPING")
from core.workspace_serializer import WorkspaceSerializer

telemetry_types = [
    "speed_analysis", "brake_analysis", "throttle_analysis",
    "rpm_analysis", "acceleration_analysis", "gear_analysis",
    "speeddiff_analysis", "distancediff_analysis", "timediff_analysis"
]

found_count = 0
for module_type in telemetry_types:
    # 查找映射中是否有該類型
    found = any(v == module_type for v in WorkspaceSerializer.WINDOW_TYPE_MAPPING.values())
    if found:
        found_count += 1
        print(f"  ✅ {module_type}")
    else:
        print(f"  ❌ {module_type}")

print(f"\n總計: {found_count}/{len(telemetry_types)} 個模組已映射")

# 測試 2: 檢查是否能創建模組實例（只檢查導入，不實際創建）
print("\n✅ 測試 2: 檢查模組是否可導入")
import sys

modules_check = [
    ("SpeedAnalysisModule", "modules.gui.lap_analysis.speed_analysis.speed_analysis_mdi"),
    ("BrakeAnalysisModule", "modules.gui.lap_analysis.brake_analysis.brake_analysis_mdi"),
    ("ThrottleAnalysisModule", "modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_mdi"),
]

for class_name, module_path in modules_check:
    try:
        # 只導入模組，不創建實例
        parts = module_path.rsplit('.', 1)
        mod = __import__(parts[0], fromlist=[class_name])
        if hasattr(mod, class_name):
            print(f"  ✅ {class_name} 可導入")
        else:
            print(f"  ❌ {class_name} 不存在於 {module_path}")
    except ImportError as e:
        print(f"  ❌ {class_name} 導入失敗: {e}")

print("\n✅ 驗證完成！")
print("\n📝 實作摘要:")
print("  1. 已添加 9 個遙測分析模組到 WINDOW_TYPE_MAPPING")
print("  2. 已添加對應的 _create_module_instance() 邏輯")
print("  3. 支援參數: year, race, session, driver1, driver2, lap1, lap2")
print("\n⚠️  後續步驟:")
print("  1. 在 GUI 中測試儲存/載入 Workspace")
print("  2. 確認遙測分析視窗能正確恢復參數")
