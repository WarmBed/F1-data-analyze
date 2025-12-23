#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Throttle Line Chart 功能測試腳本
快速驗證所有組件是否正常運作

執行方式:
    python test_throttle_line_chart.py
"""

import sys
import io
import warnings

# 設定 stdout 為 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
warnings.filterwarnings('ignore')

print("\n" + "="*80)
print("Throttle Line Chart Module Test")
print("="*80 + "\n")

# 測試 1: 導入檢查
print("[1] Testing Module Imports...")
try:
    import sys
    import os
    # 添加專案根目錄到 Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    from modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_data_loader import ThrottleLineChartDataLoader
    print("   [OK] ThrottleLineChartDataLoader")
except Exception as e:
    print(f"   [FAIL] ThrottleLineChartDataLoader: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_duration_chart_widget import ThrottleDurationChartWidget
    print("   ✅ ThrottleDurationChartWidget 導入成功")
except Exception as e:
    print(f"   ❌ ThrottleDurationChartWidget 導入失敗: {e}")
    sys.exit(1)

try:
    from modules.gui.Throttle_analysis.throttle_line_chart_analysis.lap_time_chart_widget import LapTimeChartWidget
    print("   ✅ LapTimeChartWidget 導入成功")
except Exception as e:
    print(f"   ❌ LapTimeChartWidget 導入失敗: {e}")
    sys.exit(1)

try:
    from modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_mdi import ThrottleLineChartMDI
    print("   ✅ ThrottleLineChartMDI 導入成功")
except Exception as e:
    print(f"   ❌ ThrottleLineChartMDI 導入失敗: {e}")
    sys.exit(1)

try:
    from modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_module import ThrottleLineChartModule
    print("   ✅ ThrottleLineChartModule 導入成功")
except Exception as e:
    print(f"   ❌ ThrottleLineChartModule 導入失敗: {e}")
    sys.exit(1)

# 測試 2: 數據載入器實例化
print("\n2️⃣ 測試數據載入器實例化...")
try:
    loader = ThrottleLineChartDataLoader()
    print("   ✅ 數據載入器實例化成功")
    print(f"   📊 CLI 功能: {loader.cli_function}")
    print(f"   📝 分析名稱: {loader.analysis_name}")
except Exception as e:
    print(f"   ❌ 實例化失敗: {e}")
    sys.exit(1)

# 測試 3: 模組接口驗證
print("\n3️⃣ 測試模組接口...")
try:
    module = ThrottleLineChartModule()
    print("   ✅ 模組實例化成功")
    
    # 測試方法存在性
    assert hasattr(module, 'initialize_module'), "缺少 initialize_module 方法"
    assert hasattr(module, 'get_widget'), "缺少 get_widget 方法"
    assert hasattr(module, 'get_default_size'), "缺少 get_default_size 方法"
    assert hasattr(module, 'get_window_title'), "缺少 get_window_title 方法"
    assert hasattr(module, 'cleanup'), "缺少 cleanup 方法"
    print("   ✅ 所有必要方法存在")
    
    # 測試預設大小
    default_size = module.get_default_size()
    assert isinstance(default_size, tuple), "get_default_size 應返回 tuple"
    assert len(default_size) == 2, "get_default_size 應返回 (width, height)"
    print(f"   ✅ 預設大小: {default_size}")
    
    # 測試標題
    title = module.get_window_title()
    assert isinstance(title, str), "get_window_title 應返回 str"
    print(f"   ✅ 視窗標題: {title}")
    
except Exception as e:
    print(f"   ❌ 模組接口測試失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 測試 4: 數據格式驗證
print("\n4️⃣ 測試數據格式驗證...")
try:
    import json
    import os
    
    # 尋找測試數據
    test_files = [
        "json/throttle_ratio_2025_australia_R.json",
        "json/throttle_ratio_2025_singapore_R.json",
        "json/throttle_ratio_2024_japan_R.json"
    ]
    
    test_file = None
    for f in test_files:
        if os.path.exists(f):
            test_file = f
            break
            
    if test_file:
        print(f"   📄 使用測試檔案: {test_file}")
        
        with open(test_file, 'r', encoding='utf-8') as fp:
            data = json.load(fp)
            
        # 驗證結構
        assert 'metadata' in data, "缺少 metadata"
        assert 'analysis' in data, "缺少 analysis"
        assert 'drivers' in data['analysis'], "缺少 drivers 列表"
        
        drivers_count = len(data['analysis']['drivers'])
        print(f"   ✅ JSON 結構正確 ({drivers_count} 位車手)")
        
        # 驗證車手數據
        if drivers_count > 0:
            driver = data['analysis']['drivers'][0]
            assert 'driver_code' in driver, "缺少 driver_code"
            assert 'laps' in driver, "缺少 laps"
            
            if driver['laps']:
                lap = driver['laps'][0]
                required_fields = [
                    'lap_number',
                    'full_throttle_duration_s',
                    'lap_time_seconds',
                    'compound'
                ]
                for field in required_fields:
                    assert field in lap, f"圈數據缺少 {field}"
                    
                print(f"   ✅ 車手數據格式正確")
    else:
        print("   ⚠️  未找到測試 JSON 檔案，跳過數據驗證")
        
except Exception as e:
    print(f"   ❌ 數據格式驗證失敗: {e}")
    import traceback
    traceback.print_exc()

# 測試 5: GUI 整合檢查
print("\n5️⃣ 測試 GUI 整合...")
try:
    # 檢查主程式中是否已整合
    with open('f1t_gui_main.py', 'r', encoding='utf-8') as f:
        gui_code = f.read()
        
    checks = [
        ('throttle_line_chart', "模組類型定義"),
        ('ThrottleLineChartModule', "模組導入"),
        ('_create_throttle_line_chart_window', "視窗創建方法"),
        ('"throttle_line_chart":', "i18n 翻譯")
    ]
    
    for check_str, desc in checks:
        if check_str in gui_code:
            print(f"   ✅ {desc}: 已整合")
        else:
            print(f"   ⚠️  {desc}: 未找到")
            
except Exception as e:
    print(f"   ❌ GUI 整合檢查失敗: {e}")

print("\n" + "="*80)
print("✅ 所有測試完成！")
print("="*80)
print("\n💡 下一步:")
print("   1. 啟動 GUI: python f1t_gui_main.py")
print("   2. 選擇賽事和會話")
print("   3. 點擊「油門分析」→「Throttle Line Chart」")
print("   4. 選擇車手並載入數據\n")
