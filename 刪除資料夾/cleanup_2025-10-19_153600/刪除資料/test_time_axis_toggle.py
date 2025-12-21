#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試速度分析模組的時間軸切換功能
驗證 X 軸標題從 "距離 (m)" 切換到 "時間 (秒)"
"""

import sys
import os
import io

# 設定 stdout 為 UTF-8 編碼
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 確保可以找到模組
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("[TEST] 開始測試時間軸切換...")
print(f"[TEST] Python 版本: {sys.version}")
print(f"[TEST] 工作目錄: {os.getcwd()}")

from PyQt5.QtWidgets import QApplication

print("[TEST] PyQt5 導入成功")

from modules.gui.lap_analysis.speed_analysis.speed_analysis_chart_widget import SpeedTelemetryChartWidget

print("[TEST] SpeedTelemetryChartWidget 導入成功")

def test_time_axis_toggle():
    """測試時間軸切換流程"""
    print("\n" + "="*80)
    print("[TEST] 測試時間軸切換功能")
    print("="*80)
    
    app = QApplication(sys.argv)
    
    # 創建圖表組件
    print("\n[STEP 1] 創建圖表組件...")
    chart = SpeedTelemetryChartWidget()
    print("[STEP 1] 圖表組件創建成功")
    
    # 1. 檢查初始狀態
    print("\n[STEP 1] 檢查初始狀態")
    print(f"   use_time_axis: {chart.use_time_axis}")
    print(f"   time_axis_available: {chart.time_axis_available}")
    print(f"   X 軸標題: '{chart.x_axis_title}'")
    print(f"   Y 軸標題: '{chart.y_axis_title}'")
    
    assert chart.use_time_axis == False, "初始應為距離軸"
    print(f"   [OK] use_time_axis 正確 (False)")
    
    # 2. 設定測試數據（包含時間數據）
    print("\n[STEP 2] 設定測試數據")
    distance = [0.0, 100.0, 200.0, 300.0, 400.0, 500.0]
    speed1 = [150.0, 180.0, 220.0, 250.0, 280.0, 300.0]
    speed2 = [140.0, 170.0, 210.0, 240.0, 270.0, 290.0]
    time_data = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5]
    
    chart.set_speed_data(
        distance=distance,
        driver1_speed=speed1,
        driver2_speed=speed2,
        driver1_name="VER",
        driver2_name="LEC",
        time_data=time_data
    )
    
    print(f"   distance 點數: {len(chart.distance_data)}")
    print(f"   time_data 點數: {len(chart.time_data)}")
    print(f"   time_axis_available: {chart.time_axis_available}")
    print(f"   X 軸標題: '{chart.x_axis_title}'")
    
    assert chart.time_axis_available == True, f"時間軸應該可用，但 time_axis_available={chart.time_axis_available}"
    print(f"   [OK] time_axis_available 正確 (True)")
    
    # 3. 切換到時間軸
    print("\n[STEP 3] 切換到時間軸")
    print(f"   切換前 X 軸標題: '{chart.x_axis_title}'")
    success = chart.toggle_time_axis(True)
    
    print(f"   切換結果: {success}")
    print(f"   use_time_axis: {chart.use_time_axis}")
    print(f"   切換後 X 軸標題: '{chart.x_axis_title}'")
    
    assert success == True, f"切換應該成功，但返回 {success}"
    print(f"   [OK] 切換成功")
    
    assert chart.use_time_axis == True, f"應該切換到時間軸，但 use_time_axis={chart.use_time_axis}"
    print(f"   [OK] use_time_axis 正確 (True)")
    
    # 檢查 X 軸標題
    if "時間" in chart.x_axis_title or "Time" in chart.x_axis_title or "秒" in chart.x_axis_title:
        print(f"   [OK] X 軸標題包含時間相關字詞: '{chart.x_axis_title}'")
    else:
        raise AssertionError(f"X 軸標題應包含時間，實際為: '{chart.x_axis_title}'")
    
    # 4. 切換回距離軸
    print("\n[STEP 4] 切換回距離軸")
    print(f"   切換前 X 軸標題: '{chart.x_axis_title}'")
    success = chart.toggle_time_axis(False)
    
    print(f"   切換結果: {success}")
    print(f"   use_time_axis: {chart.use_time_axis}")
    print(f"   切換後 X 軸標題: '{chart.x_axis_title}'")
    
    assert success == True, f"切換應該成功，但返回 {success}"
    print(f"   [OK] 切換成功")
    
    assert chart.use_time_axis == False, f"應該切換回距離軸，但 use_time_axis={chart.use_time_axis}"
    print(f"   [OK] use_time_axis 正確 (False)")
    
    # 檢查 X 軸標題
    if "距離" in chart.x_axis_title or "Distance" in chart.x_axis_title:
        print(f"   [OK] X 軸標題包含距離相關字詞: '{chart.x_axis_title}'")
    else:
        raise AssertionError(f"X 軸標題應包含距離，實際為: '{chart.x_axis_title}'")
    
    # 5. 測試沒有時間數據時的行為
    print("\n[STEP 5] 測試沒有時間數據時的切換")
    chart.set_speed_data(
        distance=distance,
        driver1_speed=speed1,
        driver2_speed=speed2,
        driver1_name="VER",
        driver2_name="LEC",
        time_data=None  # 不提供時間數據
    )
    
    print(f"   time_axis_available: {chart.time_axis_available}")
    
    success = chart.toggle_time_axis(True)
    print(f"   嘗試切換到時間軸: {success}")
    print(f"   use_time_axis: {chart.use_time_axis}")
    print(f"   X 軸標題: '{chart.x_axis_title}'")
    
    assert success == False, f"沒有時間數據時切換應該失敗，但返回 {success}"
    print(f"   [OK] 正確拒絕切換")
    
    assert chart.use_time_axis == False, f"應該保持距離軸，但 use_time_axis={chart.use_time_axis}"
    print(f"   [OK] 保持距離軸")
    
    print("\n" + "="*80)
    print("[SUCCESS] 所有測試通過！")
    print("="*80 + "\n")
    
    return True

if __name__ == "__main__":
    try:
        test_time_axis_toggle()
        print("\n[SUCCESS] 測試完成，退出碼 0\n")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAILED] 測試失敗: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 發生錯誤: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
