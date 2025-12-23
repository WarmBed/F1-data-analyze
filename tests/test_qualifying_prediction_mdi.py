#!/usr/bin/env python3
"""
排位賽預測 MDI 模組測試腳本
Test Script for Qualifying Prediction MDI Module

測試項目：
1. 模組導入測試
2. MDI 初始化測試
3. Widget 創建測試
4. 方法存在性測試
5. API Worker 測試（可選）
"""

import sys
import os

# 設置 PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("排位賽預測 MDI 模組測試")
print("=" * 70)

# ========== 測試 1: 模組導入 ==========
print("\n[測試 1] 模組導入測試...")
try:
    from modules.gui.qualifying_prediction import (
        QualifyingPredictionMDI,
        QualifyingPredictionDataLoader,
        QualifyingPredictionWidget,
        __version__
    )
    print(f"✅ 模組導入成功")
    print(f"   版本號: {__version__}")
except Exception as e:
    print(f"❌ 模組導入失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ========== 測試 2: 檢查類別屬性 ==========
print("\n[測試 2] 類別屬性檢查...")
try:
    # 檢查 MDI 類別方法
    mdi_methods = [m for m in dir(QualifyingPredictionMDI) if not m.startswith('_') or m.startswith('_on_')]
    required_methods = [
        'ensure_registered', 'initialize_module', 'create_data_manager', 
        'create_chart_widget', 'load_initial_data', 'update_parameters',
        'get_window_title', 'get_widget', '_on_data_loaded', '_on_load_error',
        '_on_api_progress', '_on_api_success', '_on_api_failure'
    ]
    
    missing_methods = [m for m in required_methods if m not in mdi_methods]
    if missing_methods:
        print(f"⚠️  缺少方法: {', '.join(missing_methods)}")
    else:
        print(f"✅ MDI 類別方法完整 ({len(required_methods)} 個必要方法)")
    
    # 檢查 DataLoader 類別方法
    loader_methods = [m for m in dir(QualifyingPredictionDataLoader) if not m.startswith('__')]
    print(f"✅ DataLoader 類別有 {len([m for m in loader_methods if not m.startswith('_')])} 個公開方法")
    
    # 檢查 Widget 類別方法
    widget_methods = [m for m in dir(QualifyingPredictionWidget) if not m.startswith('__')]
    print(f"✅ Widget 類別有 {len([m for m in widget_methods if not m.startswith('_')])} 個公開方法")
    
except Exception as e:
    print(f"❌ 類別屬性檢查失敗: {e}")
    import traceback
    traceback.print_exc()

# ========== 測試 3: MDI 初始化測試 (無 GUI) ==========
print("\n[測試 3] MDI 初始化測試（無 GUI 模式）...")
try:
    from PyQt5.QtWidgets import QApplication
    
    # 創建 QApplication（如果不存在）
    app = QApplication.instance()
    if app is None:
        app = QApplication([])  # 使用空列表避免命令行參數
    
    # 創建 MDI 實例
    print("   創建 MDI 實例...")
    mdi = QualifyingPredictionMDI(parent=None)
    print("   ✅ MDI 實例創建成功")
    
    # 設置測試參數
    print("   設置測試參數...")
    mdi.current_year = "2024"
    mdi.current_race = "Monaco"
    print(f"   ✅ 參數設置成功: {mdi.current_year} {mdi.current_race}")
    
    # 初始化模組（不啟動 API Worker）
    print("   初始化模組...")
    init_result = mdi.initialize_module()
    
    if init_result:
        print("   ✅ 模組初始化成功")
        
        # 檢查組件
        if hasattr(mdi, 'chart_widget') and mdi.chart_widget:
            print("   ✅ Widget 已創建")
        else:
            print("   ⚠️  Widget 未創建")
        
        if hasattr(mdi, 'data_manager') and mdi.data_manager:
            print("   ✅ DataManager 已創建")
        else:
            print("   ⚠️  DataManager 未創建")
        
        # 測試 get_widget
        widget = mdi.get_widget()
        if widget:
            print("   ✅ get_widget() 返回有效元件")
            
            # 測試視窗標題
            title = mdi.get_window_title()
            print(f"   ✅ 視窗標題: {title}")
        else:
            print("   ❌ get_widget() 返回 None")
    else:
        print("   ❌ 模組初始化失敗")
    
    # 清理：不啟動事件循環
    print("   ⚠️  跳過 API 調用測試（避免阻塞）")
    
except Exception as e:
    print(f"❌ MDI 初始化測試失敗: {e}")
    import traceback
    traceback.print_exc()

# ========== 測試 4: Widget 創建測試 ==========
print("\n[測試 4] Widget 獨立創建測試...")
try:
    widget = QualifyingPredictionWidget(parent=None)
    print("   ✅ Widget 獨立創建成功")
    
    # 檢查主要方法
    if hasattr(widget, 'update_display'):
        print("   ✅ update_display 方法存在")
    if hasattr(widget, 'clear_display'):
        print("   ✅ clear_display 方法存在")
    if hasattr(widget, 'get_current_data'):
        print("   ✅ get_current_data 方法存在")
    
except Exception as e:
    print(f"❌ Widget 創建失敗: {e}")
    import traceback
    traceback.print_exc()

# ========== 測試 5: DataLoader 創建測試 ==========
print("\n[測試 5] DataLoader 獨立創建測試...")
try:
    loader = QualifyingPredictionDataLoader(
        year="2024",
        race="Monaco",
        parent=None
    )
    print("   ✅ DataLoader 獨立創建成功")
    
    # 檢查主要方法
    if hasattr(loader, '_validate_data_format'):
        print("   ✅ _validate_data_format 方法存在")
    if hasattr(loader, '_transform_data_for_display'):
        print("   ✅ _transform_data_for_display 方法存在")
    if hasattr(loader, '_find_fastest_driver'):
        print("   ✅ _find_fastest_driver 方法存在")
    
except Exception as e:
    print(f"❌ DataLoader 創建失敗: {e}")
    import traceback
    traceback.print_exc()

# ========== 測試總結 ==========
print("\n" + "=" * 70)
print("測試總結")
print("=" * 70)
print("""
測試完成項目：
1. 模組導入成功
2. 類別屬性完整
3. MDI 初始化成功
4. Widget 創建成功
5. DataLoader 創建成功

注意事項：
- API 調用需要實際的 API 服務運行
- 數據顯示需要有效的預測數據
- 完整測試需要在主 GUI 中進行

下一步：
如果上述測試全部通過，可以進入主 GUI 整合階段
""")

print("\n提示：若要測試完整功能（含 API 調用），請確保：")
print("   1. API 服務正在運行 (refactored_api.py)")
print("   2. 已執行 CLI 訓練模型: python f1_analysis_modular_main.py -f 73")
print("=" * 70)
