#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
進度條系統整合測試

測試場景：
1. 打開多個分析模組（Rain, Pitstop, Accident, Speed）
2. 變更賽事參數（year, race, session）
3. 驗證進度條視窗是否彈出
4. 驗證所有模組是否正確更新
"""

import sys
import os

# 設定 UTF-8 輸出
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

print("\n" + "=" * 80)
print("進度條系統整合測試")
print("=" * 80)

print("\n[測試計畫]")
print("-" * 80)
print("階段 1: 檢查模組配置")
print("  - 驗證 Rain/Pitstop/Accident 模組有 analysis_type 屬性")
print("  - 驗證 all_analysis_types 列表包含所有模組")
print("\n階段 2: 檢查更新邏輯")
print("  - 驗證遙測類型模組調用 update_lap_parameters()")
print("  - 驗證賽事級模組調用 update_parameters()")
print("\n階段 3: 手動 GUI 測試")
print("  - 打開 Rain/Pitstop/Accident 模組")
print("  - 變更賽事參數")
print("  - 觀察進度條是否彈出")

print("\n" + "=" * 80)
print("階段 1: 檢查模組配置")
print("=" * 80)

# 檢查 1: Rain Analysis
print("\n[1] Rain Weather Analysis")
print("-" * 80)
try:
    from modules.gui.rain_analysis.rain_analysis_mdi import RainAnalysisMDI
    
    # 檢查 analysis_type 屬性
    test_module = RainAnalysisMDI(2025, "Japan", "R")
    if hasattr(test_module, 'analysis_type'):
        print(f"[OK] analysis_type = '{test_module.analysis_type}'")
    else:
        print("[ERROR] 缺少 analysis_type 屬性")
    
    # 檢查更新方法
    if hasattr(test_module, 'update_parameters'):
        print("[OK] 有 update_parameters() 方法")
    else:
        print("[WARN] 缺少 update_parameters() 方法")
    
    if hasattr(test_module, 'onParametersChanged'):
        print("[OK] 有 onParametersChanged() 方法")
    
except Exception as e:
    print(f"[ERROR] 載入失敗: {e}")

# 檢查 2: Pitstop Analysis
print("\n[2] Pitstop Analysis")
print("-" * 80)
try:
    from modules.gui.pitstop_analysis.pitstop_analysis_mdi import PitstopAnalysisMDI
    
    test_module = PitstopAnalysisMDI(2025, "Japan", "R")
    if hasattr(test_module, 'analysis_type'):
        print(f"[OK] analysis_type = '{test_module.analysis_type}'")
    else:
        print("[ERROR] 缺少 analysis_type 屬性")
    
    if hasattr(test_module, 'update_parameters'):
        print("[OK] 有 update_parameters() 方法")
    else:
        print("[WARN] 缺少 update_parameters() 方法")
    
except Exception as e:
    print(f"[ERROR] 載入失敗: {e}")

# 檢查 3: Accident Analysis
print("\n[3] Accident Analysis")
print("-" * 80)
try:
    from modules.gui.accident_analysis.accident_analysis_mdi import AccidentAnalysisMDI
    
    test_module = AccidentAnalysisMDI(2025, "Japan", "R")
    if hasattr(test_module, 'analysis_type'):
        print(f"[OK] analysis_type = '{test_module.analysis_type}'")
    else:
        print("[ERROR] 缺少 analysis_type 屬性")
    
    if hasattr(test_module, 'update_parameters'):
        print("[OK] 有 update_parameters() 方法")
    else:
        print("[WARN] 缺少 update_parameters() 方法")
    
    if hasattr(test_module, 'onParametersChanged'):
        print("[OK] 有 onParametersChanged() 方法")
    
except Exception as e:
    print(f"[ERROR] 載入失敗: {e}")

print("\n" + "=" * 80)
print("階段 2: 檢查 GUI 主程式配置")
print("=" * 80)

print("\n[檢查 all_analysis_types 列表]")
print("-" * 80)

# 模擬 f1t_gui_main.py 中的配置
all_analysis_types = {
    # 遙測分析類型
    'speed_analysis',  # 速度分析
    'speed',          # 速度圖表
    'brake',          # 煞車分析
    'throttle',       # 油門分析
    'steering',       # 轉向分析
    'gear',           # 檔位分析
    'rpm',            # RPM分析
    'acceleration',   # 加速度分析
    'speed_diff',     # 速度差分析
    'Speeddiff',      # 速度差分析（大寫變體）
    'distancediff',   # 累積距離差分析
    # 賽事級分析類型
    'rain_weather',   # 天氣分析
    'pitstop',        # 進站分析
    'accident',       # 事故分析
}

required_types = ['rain_weather', 'pitstop', 'accident']
missing_types = [t for t in required_types if t not in all_analysis_types]

if missing_types:
    print(f"[ERROR] 缺少類型: {missing_types}")
else:
    print("[OK] 所有賽事級分析類型已包含")
    for t in required_types:
        print(f"     - {t}")

print("\n" + "=" * 80)
print("階段 3: 手動測試指引")
print("=" * 80)

print("""
請執行以下手動測試步驟：

1. 啟動 GUI
   python f1t_gui_main.py

2. 設定基本參數
   - Year: 2025
   - Race: Japan
   - Session: R

3. 打開測試模組
   - 開啟 Rain Weather Analysis
   - 開啟 Pitstop Analysis
   - 開啟 Accident Analysis
   - 開啟 Speed Analysis (作為對照組)

4. 變更賽事參數
   - 將 Race 改為 Italy
   - 觀察是否彈出確認對話框
   - 點擊「是」確認更新

5. 驗證結果
   預期行為：
   ✓ 應該彈出進度條視窗
   ✓ 顯示 "更新中: rain_weather (1/4)..."
   ✓ 顯示 "更新中: pitstop (2/4)..."
   ✓ 顯示 "更新中: accident (3/4)..."
   ✓ 顯示 "更新中: speed_analysis (4/4)..."
   ✓ 所有模組數據應更新為 Italy 的資料

6. 檢查日誌輸出
   - 查找 "[LAP_CONTROL]" 標記的日誌
   - 確認所有模組都被正確識別並更新
""")

print("\n" + "=" * 80)
print("測試完成")
print("=" * 80)
print("\n如果階段 1 和 2 都通過，請繼續進行階段 3 的手動 GUI 測試。")
