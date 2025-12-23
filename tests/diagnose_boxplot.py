#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Lap Time Box Plot 診斷腳本

檢查點:
1. 數據管理器是否正確初始化
2. API 請求是否成功
3. 數據是否正確處理
4. 信號是否正確連接和發射
5. 圖表組件是否正確接收數據
"""

import sys
import os

# 添加專案路徑
sys.path.insert(0, os.getcwd())

from PyQt5.QtWidgets import QApplication
from modules.gui.lap_box_plot_analysis.lap_box_plot_analysis_mdi import (
    LapTimeBoxPlotAnalysis,
    LapTimeBoxPlotDataManager
)

def diagnose_lap_box_plot():
    """診斷 Lap Box Plot 模組"""
    
    print("=" * 80)
    print("🔍 Lap Time Box Plot 診斷")
    print("=" * 80)
    print()
    
    app = QApplication(sys.argv)
    
    # 1. 創建模組實例
    print("步驟 1: 創建模組實例...")
    try:
        module = LapTimeBoxPlotAnalysis()
        print("✅ 模組創建成功")
        print(f"   - 數據管理器: {module.data_manager}")
        print(f"   - 圖表組件: {module.chart_widget}")
        print(f"   - 控制組件: {module.control_widget}")
    except Exception as e:
        print(f"❌ 模組創建失敗: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print()
    
    # 2. 檢查數據管理器
    print("步驟 2: 檢查數據管理器...")
    if module.data_manager:
        print(f"✅ 數據管理器存在")
        print(f"   - 類型: {type(module.data_manager)}")
        print(f"   - 分析類型: {module.data_manager.config.analysis_type if hasattr(module.data_manager, 'config') else 'N/A'}")
        print(f"   - CLI 功能: {module.data_manager.config.cli_function if hasattr(module.data_manager, 'config') else 'N/A'}")
        print(f"   - API 端點: {module.data_manager.config.api_endpoint if hasattr(module.data_manager, 'config') else 'N/A'}")
        print(f"   - 有 load_data 方法: {hasattr(module.data_manager, 'load_data')}")
        print(f"   - 有 data_loaded 信號: {hasattr(module.data_manager, 'data_loaded')}")
    else:
        print(f"❌ 數據管理器不存在")
        return
    
    print()
    
    # 3. 檢查圖表組件
    print("步驟 3: 檢查圖表組件...")
    if module.chart_widget:
        print(f"✅ 圖表組件存在")
        print(f"   - 類型: {type(module.chart_widget)}")
        print(f"   - 有 update_data 方法: {hasattr(module.chart_widget, 'update_data')}")
        print(f"   - 有 set_data 方法: {hasattr(module.chart_widget, 'set_data')}")
    else:
        print(f"❌ 圖表組件不存在")
        return
    
    print()
    
    # 4. 檢查信號連接
    print("步驟 4: 檢查信號連接...")
    
    # 檢查 data_loaded 信號的接收者
    if hasattr(module.data_manager, 'data_loaded'):
        receivers = module.data_manager.data_loaded.receivers(module.data_manager.data_loaded)
        print(f"   - data_loaded 信號接收者數量: {receivers}")
        if receivers > 0:
            print(f"   ✅ 信號已連接")
        else:
            print(f"   ⚠️ 信號未連接!")
    
    print()
    
    # 5. 測試數據載入
    print("步驟 5: 測試數據載入 (2025 Japan R)...")
    
    # 設置信號監聽
    data_received = {'success': False, 'data': None}
    
    def on_data_loaded(data):
        print(f"   🎉 接收到 data_loaded 信號!")
        print(f"   - 數據類型: {type(data)}")
        if isinstance(data, dict):
            print(f"   - 數據鍵: {list(data.keys())}")
            print(f"   - driver_laptimes: {len(data.get('driver_laptimes', {}))} 位車手")
        data_received['success'] = True
        data_received['data'] = data
    
    def on_error(error_msg):
        print(f"   ❌ 接收到錯誤: {error_msg}")
    
    # 連接信號
    module.data_manager.data_loaded.connect(on_data_loaded)
    if hasattr(module.data_manager, 'load_error'):
        module.data_manager.load_error.connect(on_error)
    
    # 載入數據
    try:
        result = module.data_manager.load_data(
            year=2025,
            race="Japan",
            session="R"
        )
        print(f"   - load_data 返回值: {result}")
    except Exception as e:
        print(f"   ❌ load_data 失敗: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # 等待異步操作完成
    print("步驟 6: 等待數據載入完成...")
    import time
    for i in range(10):
        app.processEvents()
        time.sleep(0.5)
        if data_received['success']:
            print(f"   ✅ 數據載入成功 (耗時 {(i+1)*0.5}s)")
            break
    else:
        print(f"   ⚠️ 數據載入超時 (5秒)")
    
    print()
    
    # 7. 檢查圖表組件狀態
    print("步驟 7: 檢查圖表組件數據...")
    if hasattr(module.chart_widget, 'current_data'):
        if module.chart_widget.current_data:
            print(f"   ✅ 圖表組件有數據")
            print(f"   - 數據類型: {type(module.chart_widget.current_data)}")
        else:
            print(f"   ⚠️ 圖表組件數據為空")
    
    if hasattr(module.chart_widget, 'driver_laptimes'):
        print(f"   - driver_laptimes: {len(module.chart_widget.driver_laptimes)} 位車手")
        if module.chart_widget.driver_laptimes:
            for driver, laps in list(module.chart_widget.driver_laptimes.items())[:3]:
                print(f"     • {driver}: {len(laps)} 圈")
    
    print()
    
    # 8. 總結
    print("=" * 80)
    print("📊 診斷總結")
    print("=" * 80)
    
    checks = [
        ("模組創建", module is not None),
        ("數據管理器", module.data_manager is not None),
        ("圖表組件", module.chart_widget is not None),
        ("信號連接", receivers > 0 if hasattr(module.data_manager, 'data_loaded') else False),
        ("數據載入", data_received['success']),
        ("圖表有數據", bool(module.chart_widget.driver_laptimes) if hasattr(module.chart_widget, 'driver_laptimes') else False),
    ]
    
    for check_name, check_result in checks:
        status = "✅" if check_result else "❌"
        print(f"{status} {check_name}: {'通過' if check_result else '失敗'}")
    
    print()
    
    # 如果有錯誤,給出建議
    if not all(check_result for _, check_result in checks):
        print("🔧 建議修復:")
        if not checks[3][1]:  # 信號連接失敗
            print("   - 檢查 initialize_module() 是否正確調用")
            print("   - 檢查 _connect_data_manager_signals() 是否執行")
        if not checks[4][1]:  # 數據載入失敗
            print("   - 檢查 API 服務器是否運行")
            print("   - 檢查網絡連接")
            print("   - 檢查 API 端點配置")
        if not checks[5][1]:  # 圖表無數據
            print("   - 檢查 update_data() 是否正確調用")
            print("   - 檢查數據格式是否正確")
    
    app.quit()

if __name__ == "__main__":
    diagnose_lap_box_plot()
